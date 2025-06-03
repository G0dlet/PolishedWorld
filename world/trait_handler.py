# world/trade_handler.py
"""
Extended trade handler with currency support and logging.
"""

from evennia.contrib.game_systems.barter.barter import TradeHandler as BaseTradeHandler
from evennia.utils import logger
import datetime


class EconomicTradeHandler(BaseTradeHandler):
    """
    Extended trade handler that supports currency and logs trades.
    """
    
    def __init__(self, part_a, part_b):
        """Initialize with currency tracking."""
        super().__init__(part_a, part_b)
        
        # Track currency offers separately
        self.part_a_currency = {"gold": 0, "silver": 0, "copper": 0}
        self.part_b_currency = {"gold": 0, "silver": 0, "copper": 0}
        
        # Check for mentor relationship
        self.is_mentor_trade = (
            (hasattr(part_a.db, 'mentees') and part_b in part_a.db.mentees) or
            (hasattr(part_b.db, 'mentees') and part_a in part_b.db.mentees)
        )
    
    def offer_currency(self, party, gold=0, silver=0, copper=0):
        """
        Add currency to an offer.
        
        Args:
            party: The party making the offer
            gold (int): Gold coins to offer
            silver (int): Silver coins to offer
            copper (int): Copper coins to offer
        """
        if not party.can_afford(gold, silver, copper):
            party.msg("|rYou don't have that much money.|n")
            return False
        
        # Reset acceptance when offer changes
        self.part_a_accepted = False
        self.part_b_accepted = False
        
        if party == self.part_a:
            self.part_a_currency = {"gold": gold, "silver": silver, "copper": copper}
        elif party == self.part_b:
            self.part_b_currency = {"gold": gold, "silver": silver, "copper": copper}
        
        return True
    
    def finish(self, force=False):
        """
        Complete trade with logging.
        """
        if self.trade_started and self.part_a_accepted and self.part_b_accepted:
            # Move items
            for obj in self.part_a_offers:
                obj.location = self.part_b
            for obj in self.part_b_offers:
                obj.location = self.part_a
            
            # Move currency
            self._transfer_currency(self.part_a, self.part_b, self.part_a_currency)
            self._transfer_currency(self.part_b, self.part_a, self.part_b_currency)
            
            # Log the trade
            self.part_a.log_trade(self.part_b, self.part_a_offers, self.part_b_offers)
            self.part_b.log_trade(self.part_a, self.part_b_offers, self.part_a_offers)
            
            # Log to server for economy tracking
            self._log_to_server()
            
            # Clean up as normal
            return super().finish(force=True)
        
        return super().finish(force)
    
    def _transfer_currency(self, from_char, to_char, amount):
        """Transfer currency between characters."""
        if not any(amount.values()):
            return
        
        # Deduct from giver
        from_char.db.currency['gold'] -= amount['gold']
        from_char.db.currency['silver'] -= amount['silver']
        from_char.db.currency['copper'] -= amount['copper']
        
        # Add to receiver
        to_char.db.currency['gold'] += amount['gold']
        to_char.db.currency['silver'] += amount['silver']
        to_char.db.currency['copper'] += amount['copper']
    
    def _log_to_server(self):
        """Log trade to server for economy tracking."""
        log_msg = (
            f"TRADE: {self.part_a.key} <-> {self.part_b.key} | "
            f"A gave: {[obj.key for obj in self.part_a_offers]} + "
            f"{self.part_a_currency} | "
            f"B gave: {[obj.key for obj in self.part_b_offers]} + "
            f"{self.part_b_currency}"
        )
        logger.log_info(log_msg)
