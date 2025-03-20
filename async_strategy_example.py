import asyncio
import os
from datetime import datetime
from hyperliquid_utils import HyperliquidAuth
from hyperliquid_utils.utils.constants import TESTNET_API_URL
from hyperliquid_utils.oms.strategy_base import Strategy

class SimpleMovingAverageStrategy(Strategy):
    """Simple Moving Average Crossover Strategy
    
    This strategy calculates simple moving averages of different periods
    and executes trades when they cross.
    """
    
    def __init__(self, auth, symbol="BTC", short_period=5, long_period=20, quantity=0.01):
        """Initialize the SMA strategy with parameters."""
        # Configure URLs
        api_url = TESTNET_API_URL
        ws_url = "wss://api.hyperliquid-testnet.xyz/ws"
        
        # Initialize parent class
        super().__init__(auth, api_url, ws_url)
        
        # Strategy specific parameters
        self.symbol = symbol
        self.short_period = short_period
        self.long_period = long_period
        self.quantity = quantity
        
        # Data storage
        self.prices = []
        self.position_side = None  # 'long', 'short', or None
        self.last_trade_time = None
        self.min_trade_interval = 60  # Minimum seconds between trades
    
    async def initialize(self):
        """Initialize strategy - subscribe to necessary streams."""
        print(f"Initializing SMA strategy for {self.symbol}...")
        
        # Subscribe to market data
        await self.stream_manager.connect()
        await self.stream_manager.subscribe_trades([self.symbol], self.on_trade_update)
        
        # Subscribe to user events for position and order updates
        await self.stream_manager.subscribe_user_events(self.on_user_event)
        
        # Sync market information
        await self.order_manager.sync_markets()
        
        # Set leverage
        await self.position_manager.set_leverage(self.symbol, 2)
        
        print(f"Strategy initialized for {self.symbol}")
        return True
    
    async def on_trade_update(self, data):
        """Process trade data to update price series."""
        if "data" in data and "coin" in data and data["coin"] == self.symbol:
            trades = data.get("data", [])
            
            # Get most recent trade price
            if trades:
                latest_trade = trades[-1]
                price = float(latest_trade.get("px", 0))
                
                # Add to price history
                self.prices.append(price)
                
                # Keep only enough prices for our calculations
                max_needed = max(self.short_period, self.long_period) + 10
                if len(self.prices) > max_needed:
                    self.prices = self.prices[-max_needed:]
    
    async def on_user_event(self, data):
        """Handle user events (positions, orders, fills)."""
        event_type = data.get("type")
        
        if event_type == "positions":
            positions = data.get("data", [])
            for position in positions:
                if position.get("coin") == self.symbol:
                    size = float(position.get("szi", 0))
                    
                    # Update our position tracking
                    if size > 0:
                        self.position_side = "long"
                    elif size < 0:
                        self.position_side = "short"
                    else:
                        self.position_side = None
    
    async def on_tick(self):
        """Main strategy logic - run on each tick."""
        # Check if we have enough price data
        if len(self.prices) < max(self.short_period, self.long_period):
            return
        
        # Calculate SMAs
        short_sma = sum(self.prices[-self.short_period:]) / self.short_period
        long_sma = sum(self.prices[-self.long_period:]) / self.long_period
        
        current_price = self.prices[-1]
        
        # Check for rate limiting
        current_time = datetime.now()
        if self.last_trade_time and (current_time - self.last_trade_time).total_seconds() < self.min_trade_interval:
            return
        
        # Trading logic
        if short_sma > long_sma:  # Bullish signal
            if self.position_side != "long":
                # Close any existing short position
                if self.position_side == "short":
                    print(f"Closing short position at {current_price}")
                    await self.close_all_positions()
                
                # Open long position
                print(f"SMA Crossover: Short {short_sma:.2f} > Long {long_sma:.2f}")
                print(f"Opening long position at {current_price}")
                await self.buy(self.symbol, self.quantity)
                self.last_trade_time = current_time
        
        elif short_sma < long_sma:  # Bearish signal
            if self.position_side != "short":
                # Close any existing long position
                if self.position_side == "long":
                    print(f"Closing long position at {current_price}")
                    await self.close_all_positions()
                
                # Open short position
                print(f"SMA Crossover: Short {short_sma:.2f} < Long {long_sma:.2f}")
                print(f"Opening short position at {current_price}")
                await self.sell(self.symbol, self.quantity)
                self.last_trade_time = current_time
    
    async def on_error(self, error):
        """Handle strategy errors."""
        print(f"Strategy error: {error}")
        # In a production system, you might want to implement recovery logic here
        # or possibly stop the strategy depending on the error

async def main():
    # Get private key from environment (or use a placeholder)
    private_key = os.environ.get("HYPERLIQUID_PRIVATE_KEY", "your_private_key_here")
    
    # Initialize authentication
    auth = HyperliquidAuth(private_key, use_testnet=True)
    
    # Create strategy instance
    strategy = SimpleMovingAverageStrategy(
        auth=auth,
        symbol="BTC",
        short_period=5,   # 5-period SMA
        long_period=20,   # 20-period SMA
        quantity=0.001    # Very small quantity for testing
    )
    
    try:
        # Start strategy
        print("Starting strategy...")
        await strategy.start()
        
        # Run for a limited time for this example
        print("Strategy running. Press Ctrl+C to stop...")
        await asyncio.sleep(300)  # Run for 5 minutes
        
    except KeyboardInterrupt:
        print("\nStrategy stopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Stop strategy and cleanup
        print("Stopping strategy...")
        await strategy.stop()
        print("Strategy stopped successfully.")

if __name__ == "__main__":
    asyncio.run(main()) 