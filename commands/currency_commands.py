# commands/currency_commands.py
"""
Currency-related commands for the economy.
"""

from evennia import Command
from evennia.utils.evtable import EvTable


class CmdMoney(Command):
    """
    Check your current money.
    
    Usage:
        money
        wallet
        purse
        
    Shows your current gold, silver, and copper.
    
    Exchange rates:
        1 gold = 10 silver
        1 silver = 10 copper
    """
    
    key = "money"
    aliases = ["wallet", "purse", "coins"]
    locks = "cmd:all()"
    help_category = "Economy"
    
    def func(self):
        """Display currency."""
        caller = self.caller
        
        currency = caller.db.currency or {"gold": 0, "silver": 0, "copper": 0}
        
        # Calculate total value in copper
        total_copper = (currency['gold'] * 100 + 
                       currency['silver'] * 10 + 
                       currency['copper'])
        
        # Create display
        caller.msg("|wYour Purse:|n")
        caller.msg(f"  Gold:        {currency['gold']}")
        caller.msg(f"  Silver:     {currency['silver']}")
        caller.msg(f"  Copper:     {currency['copper']}")
        caller.msg(f"  Total value: {total_copper} copper")
        
        # Show what they can afford
        if total_copper >= 100:
            caller.msg("\n|gYou have enough for quality equipment.|n")
        elif total_copper >= 50:
            caller.msg("\n|yYou can afford basic necessities.|n")
        elif total_copper >= 10:
            caller.msg("\n|yYou have enough for simple food.|n")
        else:
            caller.msg("\n|rYou are nearly broke!|n")


class CmdOfferCurrency(Command):
    """
    Offer currency in a trade.
    
    Usage:
        offer <amount> <type>
        offer <amount> gold
        
    Examples:
        offer 5 silver
        offer 10 copper
        offer 1 gold
        
    This command is only available during an active trade.
    The currency is added to your current trade offer.
    """
    
    key = "offer gold"
    aliases = ["offer silver", "offer copper", "offer money"]
    locks = "cmd:all()"
    help_category = "Trading"
    
    def func(self):
        """Add currency to trade offer."""
        caller = self.caller
        
        if not hasattr(caller.ndb, 'tradehandler') or not caller.ndb.tradehandler:
            caller.msg("You are not in a trade.")
            return
        
        # Parse amount and type
        args = self.args.strip().split()
        if len(args) != 2:
            caller.msg("Usage: offer <amount> <currency>")
            return
        
        try:
            amount = int(args[0])
        except ValueError:
            caller.msg("Amount must be a number.")
            return
        
        currency_type = args[1].lower()
        if currency_type not in ["gold", "silver", "copper"]:
            caller.msg("Currency must be gold, silver, or copper.")
            return
        
        # Create currency offer
        handler = caller.ndb.tradehandler
        gold = amount if currency_type == "gold" else 0
        silver = amount if currency_type == "silver" else 0
        copper = amount if currency_type == "copper" else 0
        
        if handler.offer_currency(caller, gold, silver, copper):
            caller.msg(f"You offer {amount} {currency_type}.")
            handler.msg_other(caller, f"{caller.key} offers {amount} {currency_type}.")
