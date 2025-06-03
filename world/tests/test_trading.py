# world/tests/test_trading.py
"""
Tests for the trading and economy system.
"""

from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create
from typeclasses.characters import Character
from typeclasses.objects import Object


class TestTrading(EvenniaTest):
    """Test trading functionality."""
    
    def setUp(self):
        super().setUp()
        self.trader1 = create.create_object(Character, key="Trader1", location=self.room1)
        self.trader2 = create.create_object(Character, key="Trader2", location=self.room1)
        
        # Give them some items
        self.item1 = create.create_object(Object, key="sword", location=self.trader1)
        self.item2 = create.create_object(Object, key="shield", location=self.trader2)
        
        # Give them some money
        self.trader1.db.currency = {"gold": 5, "silver": 10, "copper": 20}
        self.trader2.db.currency = {"gold": 2, "silver": 5, "copper": 50}
    
    def test_currency_system(self):
        """Test currency handling."""
        # Test initial currency
        self.assertEqual(self.trader1.db.currency['gold'], 5)
        
        # Test can_afford
        self.assertTrue(self.trader1.can_afford(gold=5))
        self.assertTrue(self.trader1.can_afford(silver=50))  # 5 gold = 50 silver
        self.assertTrue(self.trader1.can_afford(gold=6))  # Can afford: 5g + 10s + 20c = 620c > 600c
        self.assertFalse(self.trader1.can_afford(gold=7))  # Cannot afford: 7g = 700c > 620c total
        
        # Test currency string
        currency_str = self.trader1.get_currency_string()
        self.assertIn("5g", currency_str)
        self.assertIn("10s", currency_str)
        self.assertIn("20c", currency_str)
    
    def test_mentor_system(self):
        """Test mentor-mentee relationships."""
        # Make trader1 a mentor
        self.trader1.skills.crafting.base = 60
        self.trader1.db.craft_counts = {"bread": 15}
        
        # Add mentee
        self.assertTrue(self.trader1.add_mentee(self.trader2))
        self.assertIn(self.trader2, self.trader1.db.mentees)
        self.assertEqual(self.trader2.db.mentor, self.trader1)
        
        # Test duplicate
        self.assertFalse(self.trader1.add_mentee(self.trader2))
        
        # Remove mentee
        self.assertTrue(self.trader1.remove_mentee(self.trader2))
        self.assertNotIn(self.trader2, self.trader1.db.mentees)
        self.assertIsNone(self.trader2.db.mentor)
    
    def test_trade_logging(self):
        """Test trade logging functionality."""
        # Log a trade
        self.trader1.log_trade(self.trader2, [self.item1], [self.item2])
        
        # Check log
        self.assertEqual(len(self.trader1.db.trade_log), 1)
        log_entry = self.trader1.db.trade_log[0]
        self.assertEqual(log_entry['partner'], 'Trader2')
        self.assertIn('sword', log_entry['gave'])
        self.assertIn('shield', log_entry['received'])
        
        # Check achievement flag
        self.assertTrue(self.trader1.db.completed_first_trade)
    
    def test_give_command_mentor(self):
        """Test giving items as a mentor."""
        # Setup mentor relationship
        self.trader1.add_mentee(self.trader2)
        
        # Test give command
        from commands.trade_commands import CmdGive
        cmd = CmdGive()
        cmd.caller = self.trader1
        cmd.args = "sword to Trader2"
        cmd.func()
        
        # Verify transfer
        self.assertEqual(self.item1.location, self.trader2)
    
    def test_money_command(self):
        """Test money display command."""
        from commands.currency_commands import CmdMoney
        cmd = CmdMoney()
        cmd.caller = self.trader1
        
        # Capture output
        old_msg = self.trader1.msg
        messages = []
        self.trader1.msg = lambda text, **kwargs: messages.append(text)
        
        cmd.func()
        
        # Check output
        output = "\n".join(messages)
        self.assertIn("Gold:        5", output)
        self.assertIn("Silver:     10", output)
        self.assertIn("Copper:     20", output)
        
        self.trader1.msg = old_msg


class TestMarketSystem(EvenniaTest):
    """Test market information system."""
    
    def setUp(self):
        super().setUp()
        self.char = create.create_object(Character, key="Merchant", location=self.room1)
    
    def test_market_overview(self):
        """Test market command."""
        from commands.trade_commands import CmdMarket
        cmd = CmdMarket()
        cmd.caller = self.char
        
        # Test basic market command
        cmd.args = ""
        cmd.func()
        # Should not error
    
    def test_trade_history(self):
        """Test trade history display."""
        # Add some mock trade data
        self.char.db.trade_log = [
            {
                'partner': 'Bob',
                'gave': ['sword'],
                'received': ['10 gold'],
                'timestamp': '2024-01-01 12:00'
            }
        ]
        
        from commands.trade_commands import CmdTradeHistory
        cmd = CmdTradeHistory()
        cmd.caller = self.char
        cmd.cmdstring = "trade history"
        
        # Capture output
        old_msg = self.char.msg
        messages = []
        self.char.msg = lambda text, **kwargs: messages.append(text)
        
        cmd.func()
        
        # Check output
        output = "\n".join(messages)
        self.assertIn("Bob", output)
        self.assertIn("sword", output)
        
        self.char.msg = old_msg
