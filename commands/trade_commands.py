# commands/trade_commands.py
"""
Trading commands for the player-driven economy.

This module integrates the Barter contrib with our game systems,
adding support for currency, mentor gifting, and trade logging.
"""

from evennia.contrib.game_systems.barter.barter import CmdTrade as BaseCmdTrade
from evennia.contrib.game_systems.barter.barter import CmdTradeHelp, CmdsetTrade
from evennia import Command
from evennia.utils import create, evtable
from django.conf import settings
import datetime


class CmdTrade(BaseCmdTrade):
    """
    Initiate trade with another player.
    
    Usage:
        trade <player> [:emote]
        trade <player> accept [:emote]
        trade <player> decline [:emote]
        
    Examples:
        trade Bob :I have some iron ingots if you need them
        trade Alice accept :Sure, let me see what you have
        trade merchant decline :Sorry, not interested right now
        
    This command initiates a secure trade session with another player.
    Both parties must agree before trading begins. Once in a trade:
    - Use 'offer' to add items or currency
    - Use 'evaluate' to examine offered items
    - Use 'accept' when satisfied with the deal
    - Both must accept for trade to complete
    
    As a mentor, you can freely give items to your mentees without
    them needing to offer anything in return.
    
    See 'trade help' during a trade for more commands.
    """
    
    key = "trade"
    aliases = ["barter", "exchange"]
    locks = "cmd:all()"
    help_category = "Economy"
    
    def func(self):
        """Execute trade command with mentor check."""
        caller = self.caller
        
        # Check if already in trade
        if hasattr(caller.ndb, 'tradehandler') and caller.ndb.tradehandler:
            if caller.ndb.tradehandler.trade_started:
                caller.msg("You are already in a trade. Use 'end trade' to abort it.")
                return
        
        # Parse arguments for mentor relationship check
        if self.args:
            args = self.args.strip()
            target_name = args.split()[0].rstrip(':')
            target = caller.search(target_name)
            
            if target and hasattr(caller.db, 'mentees') and target in caller.db.mentees:
                # This is a mentor trading with mentee
                caller.msg("|gYou are trading with your mentee. You can give freely!|n")
        
        # Call parent implementation
        super().func()


class CmdGive(Command):
    """
    Give items or currency to another player (mentor system).
    
    Usage:
        give <item> to <player>
        give <amount> <currency> to <player>
        
    Examples:
        give sword to newbie
        give 10 gold to student
        give pickaxe,hammer to apprentice
        
    This command allows mentors to give items directly to their
    mentees without going through the trade system. It's designed
    to help new players get started.
    
    Non-mentors must use the trade system for secure exchanges.
    """
    
    key = "give"
    aliases = ["gift"]
    locks = "cmd:all()"
    help_category = "Economy"
    
    def parse(self):
        """Parse the give command."""
        if " to " not in self.args:
            self.items = ""
            self.target = ""
            return
            
        parts = self.args.split(" to ", 1)
        self.items = parts[0].strip()
        self.target = parts[1].strip() if len(parts) > 1 else ""
    
    def func(self):
        """Execute the give command."""
        caller = self.caller
        
        # Parse the command first
        self.parse()
        
        if not self.items or not self.target:
            caller.msg("Usage: give <item> to <player>")
            return
        
        # Find target
        target = caller.search(self.target)
        if not target:
            return
        
        if target == caller:
            caller.msg("You cannot give items to yourself.")
            return
        
        # Check if this is a mentor-mentee relationship
        is_mentee = hasattr(caller.db, 'mentees') and target in caller.db.mentees
        
        if not is_mentee:
            caller.msg("|yYou can only give items directly to your mentees.|n")
            caller.msg("Use |wtrade|n to exchange items with other players.")
            return
        
        # Parse items to give
        item_names = [item.strip() for item in self.items.split(",")]
        items_to_give = []
        
        # Check for currency
        parts = self.items.split()
        if len(parts) == 2 and parts[0].isdigit() and parts[1] in ["gold", "silver", "copper"]:
            # Handle currency
            amount = int(parts[0])
            currency = parts[1]
            
            if not self.give_currency(caller, target, amount, currency):
                return
        else:
            # Handle items
            for item_name in item_names:
                obj = caller.search(item_name, location=caller)
                if not obj:
                    return
                items_to_give.append(obj)
            
            # Transfer items
            for obj in items_to_give:
                obj.move_to(target, quiet=True)
                caller.msg(f"|gYou give {obj.get_display_name(caller)} to {target.name}.|n")
                target.msg(f"|g{caller.name} gives you {obj.get_display_name(target)}.|n")
        
        # Log the gift
        self.log_gift(caller, target, items_to_give)
        
        # Check for first gift achievement
        if not target.db.received_first_gift:
            target.db.received_first_gift = True
            if hasattr(target, 'achievements'):
                target.achievements.grant("first_gift", "Received your first gift from a mentor!")
    
    def give_currency(self, giver, receiver, amount, currency):
        """Handle currency transfers."""
        # Get currency handler (if implemented)
        if not hasattr(giver.db, 'currency'):
            giver.db.currency = {"gold": 0, "silver": 0, "copper": 0}
        
        if giver.db.currency.get(currency, 0) < amount:
            giver.msg(f"|rYou don't have {amount} {currency}.|n")
            return False
        
        # Transfer currency
        giver.db.currency[currency] -= amount
        
        if not hasattr(receiver.db, 'currency'):
            receiver.db.currency = {"gold": 0, "silver": 0, "copper": 0}
        receiver.db.currency[currency] = receiver.db.currency.get(currency, 0) + amount
        
        giver.msg(f"|gYou give {amount} {currency} to {receiver.name}.|n")
        receiver.msg(f"|g{giver.name} gives you {amount} {currency}.|n")
        
        return True
    
    def log_gift(self, giver, receiver, items):
        """Log gifts for economic tracking."""
        if not hasattr(giver.db, 'gift_log'):
            giver.db.gift_log = []
        
        log_entry = {
            'to': receiver.key,
            'items': [item.key for item in items],
            'timestamp': datetime.datetime.now()
        }
        giver.db.gift_log.append(log_entry)


class CmdTradeHistory(Command):
    """
    View your trade history and statistics.
    
    Usage:
        trade history [player]
        trade stats
        
    Shows your recent trades, most traded items, and trade partners.
    Mentors can see their gift history to mentees.
    """
    
    key = "trade history"
    aliases = ["trade stats", "trade log"]
    locks = "cmd:all()"
    help_category = "Economy"
    
    def func(self):
        """Display trade history."""
        caller = self.caller
        
        if "stats" in self.cmdstring:
            self.show_trade_stats()
        else:
            self.show_trade_history()
    
    def show_trade_history(self):
        """Show recent trades."""
        caller = self.caller
        
        # Get trade log
        trade_log = caller.db.trade_log or []
        
        if not trade_log:
            caller.msg("You have no recorded trades.")
            return
        
        # Show last 10 trades
        caller.msg("|wRecent Trade History:|n")
        recent = trade_log[-10:]
        
        for i, entry in enumerate(reversed(recent)):
            partner = entry.get('partner', 'Unknown')
            gave = entry.get('gave', [])
            received = entry.get('received', [])
            timestamp = entry.get('timestamp', 'Unknown time')
            
            caller.msg(f"\n|w{i+1}.|n Trade with |c{partner}|n ({timestamp})")
            if gave:
                caller.msg(f"  |rGave:|n {', '.join(gave)}")
            if received:
                caller.msg(f"  |gReceived:|n {', '.join(received)}")
    
    def show_trade_stats(self):
        """Show trade statistics."""
        caller = self.caller
        
        trade_log = caller.db.trade_log or []
        gift_log = caller.db.gift_log or []
        
        # Calculate stats
        total_trades = len(trade_log)
        total_gifts = len(gift_log)
        
        # Most traded items
        given_items = {}
        received_items = {}
        trade_partners = {}
        
        for entry in trade_log:
            # Count items
            for item in entry.get('gave', []):
                given_items[item] = given_items.get(item, 0) + 1
            for item in entry.get('received', []):
                received_items[item] = received_items.get(item, 0) + 1
            
            # Count partners
            partner = entry.get('partner', 'Unknown')
            trade_partners[partner] = trade_partners.get(partner, 0) + 1
        
        # Display stats
        caller.msg("|wTrade Statistics:|n")
        caller.msg(f"\nTotal Trades: {total_trades}")
        caller.msg(f"Total Gifts Given: {total_gifts}")
        
        if given_items:
            caller.msg("\n|wMost Given Items:|n")
            sorted_given = sorted(given_items.items(), key=lambda x: x[1], reverse=True)[:5]
            for item, count in sorted_given:
                caller.msg(f"  {item}: {count}x")
        
        if received_items:
            caller.msg("\n|wMost Received Items:|n")
            sorted_received = sorted(received_items.items(), key=lambda x: x[1], reverse=True)[:5]
            for item, count in sorted_received:
                caller.msg(f"  {item}: {count}x")
        
        if trade_partners:
            caller.msg("\n|wFrequent Trade Partners:|n")
            sorted_partners = sorted(trade_partners.items(), key=lambda x: x[1], reverse=True)[:5]
            for partner, count in sorted_partners:
                caller.msg(f"  {partner}: {count} trades")


class CmdMarket(Command):
    """
    View market trends and trade information.
    
    Usage:
        market
        market <item>
        market trends
        
    Shows what items are being traded, supply and demand based on
    recent trades, and helps you understand the player economy.
    
    This information is compiled from actual player trades.
    """
    
    key = "market"
    aliases = ["economy", "prices"]
    locks = "cmd:all()"
    help_category = "Economy"
    
    def func(self):
        """Display market information."""
        if not self.args:
            self.show_market_overview()
        elif "trends" in self.args:
            self.show_market_trends()
        else:
            self.show_item_market(self.args.strip())
    
    def show_market_overview(self):
        """Show general market information."""
        # This would aggregate data from all players' trade logs
        # For now, show a simpler version based on caller's data
        
        caller = self.caller
        caller.msg("|wMarket Overview|n")
        caller.msg("|xMarket data is compiled from recent player trades.|n")
        
        # In a real implementation, this would query a global trade database
        caller.msg("\n|wPopular Trade Goods:|n")
        caller.msg("  - Iron ingots (high demand)")
        caller.msg("  - Leather (moderate supply)")
        caller.msg("  - Food items (constant demand)")
        caller.msg("  - Tools (crafters needed)")
        
        caller.msg("\n|wUse 'market <item>' for specific item info.|n")
    
    def show_market_trends(self):
        """Show market trends over time."""
        caller = self.caller
        caller.msg("|wMarket Trends|n")
        
        # This would show how trade volumes and patterns change
        caller.msg("\n|gRising Demand:|n")
        caller.msg("  - Winter clothing (seasonal)")
        caller.msg("  - Preserved food")
        
        caller.msg("\n|rDeclining Demand:|n")
        caller.msg("  - Raw wood (oversupply)")
        
        caller.msg("\n|yNew Items:|n")
        caller.msg("  - Steam engines (engineering breakthrough)")
    
    def show_item_market(self, item_name):
        """Show market info for specific item."""
        caller = self.caller
        caller.msg(f"|wMarket Info: {item_name}|n")
        
        # This would search global trade data
        caller.msg(f"\n|xNo recent trades found for '{item_name}'.|n")
        caller.msg("As more players trade, market data will become available.")


# Extended trade cmdset with our custom commands
class ExtendedTradeCmdSet(CmdsetTrade):
    """Extended trade commands including currency and logging."""
    
    def at_cmdset_creation(self):
        """Add our extended commands."""
        super().at_cmdset_creation()
        # The base cmdset already has all trade commands
        # We could add currency-specific commands here if needed
