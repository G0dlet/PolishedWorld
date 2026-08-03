"""
Player-facing currency commands (Stage 4, Component B).

Three commands: `wallet` reads a balance (B.1), `pay` moves one (B.2), and
`@economy` (C.2) is the admin surface -- the only place in the game where money
is created or destroyed. The temple faucet (`work`, D.1) and the barter bridge
(E) come later and are deliberately not anticipated here.

⚠️ `CmdEconomy.func()` contains the codebase's ONLY production call to
`CurrencyHandler.add()`. That is the whole of S4-1 expressed as a fact about one
function. If a second call site for `add()` ever appears anywhere outside this
module, the mint invariant is gone and `@economy audit` is the only thing that
will notice.

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
from evennia.utils import logger

from typeclasses.treasury import (
    PROBLEM_NOT_FOUND,
    PROBLEM_UNSET,
    PROBLEM_WRONG_TYPE,
    TREASURY_DBREF_SETTING,
    get_configured_dbref,
    resolve_treasury,
)
from world import economy_log
from world.currency import format_copper, format_gamegold, parse_amount


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


# --------------------------------------------------------------------------
# Admin surface (C.2)
# --------------------------------------------------------------------------
#
# WHY THIS COMMAND IS SHAPED THE WAY IT IS
# ----------------------------------------
# `@economy mint` is the single production caller of the mint primitive, so the
# entire integrity of the money supply rests on this one function being hard to
# invoke by accident and impossible to invoke ambiguously. Three design decisions
# carry that weight:
#
# 1. CONFIRMATION IS ARGUMENT-BASED, AND THE BARE FORM IS A DRY RUN.
#    `@economy mint 100 gold` creates nothing -- it renders what WOULD happen,
#    including the resulting reserve obligation. `@economy mint 100 gold confirm`
#    executes. The protection is not the word `confirm`; it is that the admin
#    sees the obligation figure they are committing to BEFORE the commitment
#    exists, which is exactly the discipline S4-1 asks for ("mint only as much
#    Gold as can actually be backed").
#
#    Rejected alternatives, so nobody re-opens this cheaply:
#    * An ndb two-step (`mint ...` then `confirm`) puts mutable pending state on
#      the most dangerous command in the game and needs a timeout, or a forgotten
#      intent sits waiting for an unrelated `confirm`.
#    * A `yield` prompt would be this codebase's first yield point. Component B
#      declined one for `pay` and established "no yields" as a house rule; mint
#      has no check/debit gap for S4-R1 to protect, but spending the precedent
#      here buys nothing the dry run does not already give. (Note for testers:
#      `.call()` on a yielding command needs `inputs=[...]` -- another cost
#      avoided.)
#
# 2. THE RESERVE OBLIGATION IS SHOWN EVERY TIME, AND IS DERIVED.
#    It appears on the bare `@economy` overview, in both previews and on both
#    receipts. A number you have to ask for is a number you forget. It costs
#    nothing to show because it is not stored anywhere: the obligation IS
#    `net_issued()` rendered in GameGold, since by S4-1 every minted Copper is
#    backed and every burn releases backing. Nothing to drift, nothing to
#    migrate.
#
# 3. A MISCONFIGURED TREASURY REFUSES THE MINT, LOUDLY AND SPECIFICALLY.
#    `resolve_treasury()` distinguishes unset, dangling and wrong-typeclass
#    because the fixes differ, and this command is where an admin first meets the
#    system -- the error message is the documentation. Minting with no Treasury
#    resolved is never allowed to fall back to the caller's own purse: that would
#    be a second mint destination and S4-1 would be gone without a test failing.
#
# DELIBERATE DEVIATION FROM THE DECOMPOSITION, FLAGGED
# ----------------------------------------------------
# §6/C lists only `audit` and `mint`. This command also implements `burn`,
# Treasury-only. Reasons: the obligation figure can currently only ever rise, so
# the decrement path has never been exercised outside a unit test; `burn()` is
# the Stage 8 exchange-back consumer and Stage 8 is far away; and the Stage 4
# exchange-back is documented as a manual admin procedure, which without a
# command means an admin destroying money with `@py` -- money moving outside the
# audited surface, which is the exact hole the audit exists to close.
#
# What `burn` deliberately does NOT support is a `from <target>` form. Burning
# out of a player's wallet is confiscation: a moderation tool, not an economy
# tool, and it needs its own design conversation.
#
# KNOWN GAP, STATED RATHER THAN PAPERED OVER
# ------------------------------------------
# The ledger entry shape (A.3) records the *recipient* of a mint but not the
# *actor* who ordered it, so the ledger alone cannot answer "which admin minted
# this?". Changing the entry shape is a Component A change and is not being made
# mid-stage; instead every mint and burn is written to Evennia's rotating log
# with the caller named, so the trail exists today. An `actor` field belongs in
# docs/BACKLOG.md -> Component F.
#
# There is also no command for moving money FROM a player INTO the Treasury:
# `CmdPay` refuses it (the `has_account` guard, whose comment already anticipates
# this) and `donate` was deliberately not claimed (decomposition §5). Stage 8's
# `exchange` command owns that direction. Not a gap to fill speculatively.


# The one mint source and the one burn reason this command uses. Both are
# validated inside CurrencyHandler against MINT_SOURCES / BURN_REASONS; naming
# them here as constants means a typo is a NameError at import rather than a
# ValueError traceback in an admin's face at the moment they mint.
_MINT_SOURCE = "crypto_exchange"
_BURN_REASON = "crypto_exchange"

# The literal token that turns a dry run into an execution.
_CONFIRM_TOKEN = "confirm"


class CmdEconomy(Command):
    """
    Inspect, mint and burn the game's money supply (Developer only)

    Usage:
        @economy
        @economy audit
        @economy mint <amount> <denomination> [confirm]
        @economy burn <amount> <denomination> [confirm]

    Examples:
        @economy
        @economy audit
        @economy mint 100 gold
        @economy mint 100 gold confirm

    `@economy` on its own shows the Treasury balance, the total ever minted and
    burned, how much is in circulation, and the GameGold reserve obligation that
    circulation represents.

    `@economy audit` recomputes the invariant that every unit of money in the
    world traces back to a recorded mint. Run it after anything unusual.

    `@economy mint` is the bootstrap tranche -- the ONE way money enters the
    world. It mints into the Treasury, never into you, and the temple faucet then
    pays players by transferring out of the Treasury. Without `confirm` it only
    shows you what would happen; nothing is created until you repeat the command
    with `confirm` on the end.

    Mint only as much Gold as you can actually back with staked GameGold. The
    obligation figure in the preview is the promise you are making.

    `@economy burn` destroys money from the Treasury, releasing the matching
    reserve obligation. It is the exchange-back direction and takes the same
    `confirm`.
    """

    key = "@economy"
    locks = "cmd:perm(Developer)"
    help_category = "Admin"

    _USAGE = (
        "Usage: |w@economy|n | |w@economy audit|n | "
        "|w@economy mint <amount> <denomination> [confirm]|n | "
        "|w@economy burn <amount> <denomination> [confirm]|n"
    )

    _RULE = "|g" + "=" * 52 + "|n"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            self._show_overview()
            return

        # split(None, 1): subcommand plus everything else untouched, so the
        # amount half reaches parse_amount with its own spacing intact.
        parts = args.split(None, 1)
        subcommand = parts[0].lower()
        remainder = parts[1].strip() if len(parts) > 1 else ""

        if subcommand == "audit":
            self._show_audit()
        elif subcommand in ("mint", "burn"):
            self._mint_or_burn(subcommand, remainder)
        else:
            caller.msg(f"Unknown subcommand '|w{subcommand}|n'.\n{self._USAGE}")

    # -- treasury reporting ------------------------------------------------

    def _treasury_problem_message(self, problem):
        """
        Explain a failed Treasury lookup in terms of the fix, not the symptom.

        This is an admin's first contact with the currency system, so the message
        IS the documentation. Each branch names the setting key and the concrete
        next action; "no Treasury configured" on its own would leave someone
        guessing which of three different situations they are in.

        Args:
            problem (str): a `PROBLEM_*` code from `resolve_treasury()`.

        Returns:
            str: a coloured, multi-line explanation.
        """
        if problem == PROBLEM_UNSET:
            return (
                f"|rNo Treasury configured.|n |w{TREASURY_DBREF_SETTING}|n is unset in "
                "server/conf/settings.py.\n"
                "  Create one, then point the setting at it and reload:\n"
                "    |w@create/drop temple treasury:typeclasses.treasury.Treasury|n\n"
                f"    |w{TREASURY_DBREF_SETTING} = \"#<dbref>\"|n\n"
                "    |w@reload|n\n"
                "  Until then the temple faucet has no funds and minting is refused."
            )

        configured = get_configured_dbref()

        if problem == PROBLEM_NOT_FOUND:
            return (
                f"|r{TREASURY_DBREF_SETTING} is set to |w{configured!r}|r but nothing with "
                "that dbref exists.|n\n"
                "  The object was deleted, or the dbref is wrong. Check with "
                f"|w@examine {configured}|n."
            )

        if problem == PROBLEM_WRONG_TYPE:
            return (
                f"|r{TREASURY_DBREF_SETTING} is set to |w{configured!r}|r, which is NOT a "
                "Treasury.|n\n"
                "  Minting is refused rather than risked: a dbref pointing at a "
                "character\n"
                "  would create money directly in someone's purse. Check with "
                f"|w@examine {configured}|n."
            )

        # Defensive: a problem code this method has not been taught. Better a
        # vague sentence than a KeyError inside the money command.
        return f"|rTreasury lookup failed ({problem}).|n"

    def _show_overview(self):
        """
        The bare `@economy` view: what exists, and what backs it.

        Deliberately does NOT run `audit()`. The overview is a cheap read of the
        ledger's own running totals, while the audit enumerates every wallet in
        the database -- folding them together would make the common call the
        expensive one and blur two different questions ("how much money is
        there?" versus "does it all trace to a mint?"). The footer points at the
        audit instead.
        """
        caller = self.caller
        treasury, problem = resolve_treasury()

        minted = economy_log.total_minted()
        burned = economy_log.total_burned()
        circulating = economy_log.net_issued()

        lines = [f"\n|wEconomy|n\n{self._RULE}"]

        if treasury is None:
            lines.append("  " + self._treasury_problem_message(problem))
        else:
            lines.append(
                f"  |yTreasury:|n            {treasury.currency.format()} "
                f"({treasury.get_display_name(caller)})"
            )

        lines.extend(
            [
                f"  |yMinted (total):|n      {format_copper(minted)}",
                f"  |yBurned (total):|n      {format_copper(burned)}",
                f"  |yIn circulation:|n      {format_copper(circulating)}",
                # The obligation is the whole point of showing this view at all:
                # it is the promise the game has made to whoever holds GameGold.
                f"  |yReserve obligation:|n  {format_gamegold(circulating)}",
                self._RULE,
                "  Run |w@economy audit|n to verify the invariant.",
            ]
        )

        caller.msg("\n".join(lines))

    def _show_audit(self):
        """
        Render the invariant, quietly when it holds and unmissably when it does not.

        `audit_report()` is uncoloured by design (D2) because it also goes into
        logs and `@py` output. The loud failure rendering is therefore this
        command's job, not the report's -- an audit failure means money was
        created or destroyed outside the mint path, the most serious class of bug
        this project can have, and it must not read like a rounding notice.
        """
        caller = self.caller
        result = economy_log.audit()
        report = economy_log.audit_report()

        if result["ok"]:
            caller.msg(f"\n{report}\n|g  Every unit of money traces to a recorded mint.|n")
            return

        # "!" rather than any pipe character: the Evennia colour parser treats a
        # raw "|" as the start of a markup code (Evennia Reference on colour
        # codes), so pipes in ASCII art silently eat the next character.
        banner = "|r" + "!" * 52 + "|n"
        caller.msg(
            f"\n{banner}\n"
            "|rECONOMY AUDIT FAILED -- money exists that no mint accounts for,|n\n"
            "|ror minted money has gone missing. Investigate before minting more.|n\n"
            f"{banner}\n"
            f"{report}\n"
            f"{banner}"
        )

    # -- mint / burn -------------------------------------------------------

    def _mint_or_burn(self, action, remainder):
        """
        Shared path for both directions of the money supply.

        One method rather than two because the guard chain is identical and
        divergence between the two would be the bug: a `burn` that validated its
        input less carefully than `mint` is a way to destroy an unintended amount.
        The three points where they differ are marked.

        GUARD ORDER, AND WHY (the Component B pattern)
        ----------------------------------------------
        Every raising path in `CurrencyHandler` needs a guard here BEFORE the
        call, or an admin typo surfaces as a traceback:

            * non-int amount   -> parse_amount only ever returns int or None
            * amount <= 0      -> the explicit check below
            * bad source/reason -> module constants, not user input
            * no wallet on target -> impossible; resolve_treasury() has already
              proved the target is a Treasury, which always has a handler

        Cheap local validation runs before anything that touches the database, so
        a malformed amount is reported as a malformed amount rather than as a
        Treasury problem the admin does not have.

        Args:
            action (str): "mint" or "burn".
            remainder (str): everything after the subcommand.
        """
        caller = self.caller
        minting = action == "mint"
        usage = f"Usage: |w@economy {action} <amount> <denomination> [confirm]|n"

        if not remainder:
            caller.msg(usage)
            return

        tokens = remainder.split()

        # `len(tokens) > 1` matters: for a bare `@economy mint confirm` the token
        # must NOT be stripped as a confirmation, or parse_amount receives an
        # empty string and the admin gets a confusing error about an amount they
        # never typed. Left in place, it fails as an unreadable amount, which is
        # what it is.
        confirmed = len(tokens) > 1 and tokens[-1].lower() == _CONFIRM_TOKEN
        if confirmed:
            tokens = tokens[:-1]

        amount = parse_amount(" ".join(tokens))
        if amount is None:
            caller.msg(
                f"'|w{' '.join(tokens)}|n' isn't an amount I can read. Name the "
                "denomination, like |w100 gold|n or |w50 copper|n.\n" + usage
            )
            return

        if amount <= 0:
            # parse_amount cannot return a negative, but "0 gold" parses fine and
            # is not an amount of money to create or destroy. <= keeps the guard
            # total rather than depending on that upstream detail holding.
            verb = "Minting" if minting else "Burning"
            caller.msg(f"{verb} nothing is not an operation.")
            return

        treasury, problem = resolve_treasury()
        if treasury is None:
            # Refusal, never a fallback. Minting into the caller's own wallet
            # would be a second mint destination and S4-1 would be silently gone.
            caller.msg(
                f"|rCannot {action}:|n no usable Treasury.\n"
                + self._treasury_problem_message(problem)
            )
            return

        balance = treasury.currency.value
        circulating = economy_log.net_issued()

        if minting:
            balance_after = balance + amount
            circulating_after = circulating + amount
        else:
            balance_after = balance - amount
            circulating_after = circulating - amount

        if not confirmed:
            self._show_preview(
                action, amount, balance, balance_after, circulating, circulating_after
            )
            return

        # ---- execution ----
        if minting:
            # ⚠️ THE ONLY PRODUCTION CALL TO add() IN THE CODEBASE (S4-1).
            new_balance = treasury.currency.add(amount, source=_MINT_SOURCE)
        else:
            if not treasury.currency.burn(amount, reason=_BURN_REASON):
                # `burn()` returns False for exactly one reason -- insufficient
                # funds (D7) -- and mutates nothing when it does. Every other
                # failure mode raises and has been screened out above.
                caller.msg(
                    f"|rThe Treasury holds only {treasury.currency.format()};|n "
                    f"cannot burn {format_copper(amount)}."
                )
                return
            new_balance = treasury.currency.value

        # The ledger records the recipient but not the actor, so this log line is
        # the only place the *who* is preserved. See the module-level note on the
        # missing `actor` field.
        logger.log_info(
            f"@economy {action}: {amount} copper by {caller.key}({caller.dbref}) "
            f"-> treasury {treasury.dbref}; treasury now {new_balance} copper, "
            f"circulation {economy_log.net_issued()} copper."
        )

        verb = "Minted" if minting else "Burned"
        caller.msg(
            f"\n|w{verb} {format_copper(amount)}.|n\n{self._RULE}\n"
            f"  |yTreasury:|n            {format_copper(new_balance)}\n"
            f"  |yIn circulation:|n      {format_copper(economy_log.net_issued())}\n"
            f"  |yReserve obligation:|n  {format_gamegold(economy_log.net_issued())}\n"
            f"{self._RULE}"
        )

    def _show_preview(
        self, action, amount, balance, balance_after, circulating, circulating_after
    ):
        """
        The dry run. This is where the real protection lives.

        Showing the obligation *before* the money exists is what makes the
        confirmation meaningful -- the admin reads the promise, then decides. The
        header states plainly that nothing has happened, because a preview that
        looks like a receipt is worse than no preview.

        For a burn, the insufficient-funds case is *reported* here but not
        *decided* here: reading the balance to phrase a warning is safe, whereas
        using this read to authorise the later debit would be the check-here-
        commit-there shape S4-R1 forbids. `burn()` re-checks under its own atomic
        section and is the only authority on whether it succeeds.
        """
        caller = self.caller
        minting = action == "mint"
        headline = (
            "MINT PREVIEW -- nothing has been created yet"
            if minting
            else "BURN PREVIEW -- nothing has been destroyed yet"
        )

        lines = [
            f"\n|y{headline}|n\n{self._RULE}",
            f"  |yAmount:|n               {format_copper(amount)}",
            f"  |yTreasury now:|n         {format_copper(balance)}",
            f"  |yTreasury after:|n       {format_copper(balance_after)}",
            f"  |yObligation now:|n       {format_gamegold(circulating)}",
            f"  |yObligation after:|n     {format_gamegold(circulating_after)}",
        ]

        if minting:
            lines.append(
                "  |rYou must be able to back the figure above with staked GameGold.|n"
            )
        elif balance < amount:
            lines.append(
                f"  |rThe Treasury holds only {format_copper(balance)} -- this burn "
                "would be refused.|n"
            )

        lines.extend(
            [
                self._RULE,
                f"  Confirm with: |w@economy {action} "
                f"{amount} copper {_CONFIRM_TOKEN}|n",
            ]
        )

        caller.msg("\n".join(lines))
