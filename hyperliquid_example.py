import asyncio
import os
from hyperliquid_utils import HyperliquidAuth, make_request_async
from hyperliquid_utils.utils.constants import TESTNET_API_URL
from hyperliquid_utils.streams.stream_manager import StreamManager
from hyperliquid_utils.oms.order_manager import OrderManager
from hyperliquid_utils.oms.position_manager import PositionManager

# Sample strategy using async patterns
class SimpleArbitrageStrategy:
    def __init__(self, auth, symbols=None):
        self.auth = auth
        self.api_url = TESTNET_API_URL  # Use testnet for safety
        self.ws_url = "wss://api.hyperliquid-testnet.xyz/ws"
        self.symbols = symbols or ["BTC", "ETH"]  # Default symbols
        self.order_manager = OrderManager(auth, self.api_url, self.ws_url)
        self.position_manager = PositionManager(self.order_manager)
        self.stream_manager = StreamManager(self.ws_url, auth)
        
    async def setup(self):
        """Initialize strategy components."""
        # Start order manager
        await self.order_manager.start()
        
        # Connect to websocket streams
        await self.stream_manager.connect()
        
        # Subscribe to market data
        await self.stream_manager.subscribe_orderbook(
            self.symbols, 
            self.on_orderbook_update
        )
        
        # Subscribe to trade updates
        await self.stream_manager.subscribe_trades(
            self.symbols,
            self.on_trade_update
        )
        
        # Subscribe to user events (positions, orders, etc.)
        await self.stream_manager.subscribe_user_events(
            self.on_user_event
        )
        
        print(f"Strategy setup complete for symbols: {self.symbols}")
        
    async def on_orderbook_update(self, data):
        """Handle order book updates."""
        # Just print a simplified version of the order book
        if "data" in data and "coin" in data:
            symbol = data["coin"]
            book = data.get("data", {})
            
            # Get best bid/ask
            bids = book.get("bids", [])
            asks = book.get("asks", [])
            
            if bids and asks:
                best_bid = bids[0] if bids else [0, 0]
                best_ask = asks[0] if asks else [0, 0]
                print(f"{symbol} Orderbook: Bid {best_bid[0]} ({best_bid[1]}) | Ask {best_ask[0]} ({best_ask[1]})")
                
                # Simple arbitrage logic (for demonstration)
                spread = (float(best_ask[0]) - float(best_bid[0])) / float(best_ask[0]) * 100
                if spread > 0.5:  # If spread is more than 0.5%
                    print(f"Potential arbitrage opportunity on {symbol}: {spread:.2f}% spread")
    
    async def on_trade_update(self, data):
        """Handle trade updates."""
        if "data" in data and "coin" in data:
            symbol = data["coin"]
            trades = data.get("data", [])
            
            for trade in trades:
                side = "BUY" if trade.get("is_buy") else "SELL"
                price = trade.get("px", 0)
                size = trade.get("sz", 0)
                print(f"{symbol} Trade: {side} {size} @ {price}")
    
    async def on_user_event(self, data):
        """Handle user events (positions, orders, fills)."""
        event_type = data.get("type")
        
        if event_type == "positions":
            positions = data.get("data", [])
            for position in positions:
                symbol = position.get("coin", "")
                size = position.get("szi", 0)
                entry_price = position.get("entry_px", 0)
                print(f"Position update: {symbol} Size: {size} Entry: {entry_price}")
                
        elif event_type == "fills":
            fills = data.get("data", [])
            for fill in fills:
                symbol = fill.get("coin", "")
                side = "BUY" if fill.get("is_buy") else "SELL"
                price = fill.get("px", 0)
                size = fill.get("sz", 0)
                print(f"Fill: {symbol} {side} {size} @ {price}")
                
        elif event_type == "orders":
            orders = data.get("data", [])
            for order in orders:
                symbol = order.get("coin", "")
                side = "BUY" if order.get("is_buy") else "SELL"
                status = order.get("status", "")
                print(f"Order update: {symbol} {side} Status: {status}")
    
    async def place_test_orders(self):
        """Place some test orders to demonstrate the OMS functionality."""
        # Get market information first
        await self.order_manager.sync_markets()
        
        for symbol in self.symbols:
            # Set leverage
            await self.position_manager.set_leverage(symbol, 5)
            
            # Place a limit buy
            print(f"Placing limit buy for {symbol}...")
            order = await self.position_manager.open_position(
                symbol=symbol,
                side="b",  # buy
                qty=0.01,  # small quantity for testing
                price=30000 if symbol == "BTC" else 2000,  # Intentionally low for safety
                order_type="limit"
            )
            
            if order:
                print(f"Limit buy placed for {symbol}: {order.order_id}")
                
                # Wait a bit then cancel
                await asyncio.sleep(2)
                print(f"Cancelling order for {symbol}...")
                await self.order_manager.cancel_order(order.order_id)
                print(f"Order cancelled for {symbol}")
    
    async def cleanup(self):
        """Cleanup resources."""
        # Cancel all orders
        await self.order_manager.cancel_all_orders()
        
        # Close positions
        await self.position_manager.close_all_positions()
        
        # Close streams
        await self.stream_manager.close()
        
        # Stop order manager
        await self.order_manager.stop()

async def main():
    # This would be your private key - DO NOT commit this to version control
    # Replace with environment variable or secure storage in production
    private_key = os.environ.get("HYPERLIQUID_PRIVATE_KEY", "your_private_key_here")
    
    # Create auth object
    auth = HyperliquidAuth(private_key, use_testnet=True)
    
    # Example API call to get market metadata
    print("Getting market metadata...")
    result = await make_request_async("GET", "/info/meta", TESTNET_API_URL)
    
    # Print available markets
    print("\nAvailable markets:")
    for asset in result.get("assetInfos", []):
        name = asset.get("name", "Unknown")
        print(f"- {name}")
    
    # Create and run simple strategy
    print("\nInitializing strategy...")
    strategy = SimpleArbitrageStrategy(auth, symbols=["BTC", "ETH"])
    
    try:
        # Setup strategy
        await strategy.setup()
        
        # Place some test orders
        # Uncomment to actually place orders - make sure you're using testnet!
        # await strategy.place_test_orders()
        
        # Keep running for a bit to receive data
        print("\nRunning strategy for 30 seconds...")
        await asyncio.sleep(30)
        
    except Exception as e:
        print(f"Error during strategy execution: {e}")
    finally:
        # Cleanup resources
        print("\nCleaning up...")
        await strategy.cleanup()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(main()) 