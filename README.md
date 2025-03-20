# Hyperliquid Trading Library

A Python library for interacting with the Hyperliquid derivatives exchange API, supporting both synchronous and asynchronous operations.

## Features

- REST API client for market data and trading
- WebSocket streaming for real-time market and user data
- Position and order management systems
- Strategy framework for building trading bots
- Full support for async/await patterns

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/library-hyperliquid.git
cd library-hyperliquid

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

## Configuration

To use the API, you'll need an API key (private key) from Hyperliquid. Set this as an environment variable:

```bash
# For Linux/Mac
export HYPERLIQUID_PRIVATE_KEY="your_private_key_here"

# For Windows PowerShell
$env:HYPERLIQUID_PRIVATE_KEY="your_private_key_here"
```

## Basic Usage

### REST API Example

```python
import asyncio
from hyperliquid_utils import HyperliquidAuth, make_request, make_request_async
from hyperliquid_utils.utils.constants import TESTNET_API_URL

# Synchronous API call
auth = HyperliquidAuth("your_private_key", use_testnet=True)
market_data = make_request("GET", "/info/meta", TESTNET_API_URL)
print(market_data)

# Asynchronous API call
async def get_market_data():
    auth = HyperliquidAuth("your_private_key", use_testnet=True)
    market_data = await make_request_async("GET", "/info/meta", TESTNET_API_URL)
    print(market_data)

asyncio.run(get_market_data())
```

### WebSocket Streaming Example

```python
import asyncio
from hyperliquid_utils import HyperliquidAuth
from hyperliquid_utils.streams.stream_manager import StreamManager

async def handle_orderbook(data):
    print(f"Orderbook update: {data}")

async def main():
    auth = HyperliquidAuth("your_private_key", use_testnet=True)
    ws_url = "wss://api.hyperliquid-testnet.xyz/ws"
    
    # Create stream manager
    stream_manager = StreamManager(ws_url, auth)
    
    # Connect to WebSocket
    await stream_manager.connect()
    
    # Subscribe to orderbook updates
    await stream_manager.subscribe_orderbook(["BTC", "ETH"], handle_orderbook)
    
    # Keep connection alive
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await stream_manager.close()

asyncio.run(main())
```

### Order Management Example

```python
import asyncio
from hyperliquid_utils import HyperliquidAuth
from hyperliquid_utils.oms.order_manager import OrderManager
from hyperliquid_utils.oms.position_manager import PositionManager

async def main():
    auth = HyperliquidAuth("your_private_key", use_testnet=True)
    api_url = "https://api.hyperliquid-testnet.xyz/api"
    ws_url = "wss://api.hyperliquid-testnet.xyz/ws"
    
    # Create order manager
    order_manager = OrderManager(auth, api_url, ws_url)
    
    # Start order manager
    await order_manager.start()
    
    # Create position manager
    position_manager = PositionManager(order_manager)
    
    # Set leverage for BTC
    await position_manager.set_leverage("BTC", 5)
    
    # Open a long position
    position = await position_manager.open_position(
        symbol="BTC",
        side="b",  # buy
        qty=0.01,
        price=None,  # Market order
        order_type="market"
    )
    
    print(f"Position opened: {position}")
    
    # Wait a bit
    await asyncio.sleep(5)
    
    # Close all positions
    await position_manager.close_all_positions()
    
    # Stop order manager
    await order_manager.stop()

asyncio.run(main())
```

## Trading Strategy Implementation

The library includes a strategy framework that makes it easy to implement trading algorithms:

```python
from hyperliquid_utils import HyperliquidAuth
from hyperliquid_utils.oms.strategy_base import Strategy

class SimpleStrategy(Strategy):
    async def initialize(self):
        # Subscribe to required streams
        await self.stream_manager.connect()
        await self.stream_manager.subscribe_trades(["BTC"], self.on_trade_update)
        
        # Set up initial position parameters
        await self.position_manager.set_leverage("BTC", 5)
        return True
    
    async def on_trade_update(self, data):
        # Process trade data
        print(f"Trade update: {data}")
    
    async def on_tick(self):
        # Main strategy logic runs here
        await self.buy("BTC", 0.01)

# Create and run strategy
auth = HyperliquidAuth("your_private_key", use_testnet=True)
strategy = SimpleStrategy(auth)
await strategy.start()
```

See the `async_strategy_example.py` file for a complete example of a moving average crossover strategy.

## Examples

For more examples, check the example scripts:
- `hyperliquid_example.py` - Basic API usage and streaming data
- `async_strategy_example.py` - Implementation of a trading strategy

## API Reference

### Main Components

- `HyperliquidAuth` - Authentication handler
- `StreamManager` - WebSocket stream subscription manager
- `OrderManager` - Order execution and tracking
- `PositionManager` - Position management and tracking
- `Strategy` - Base class for trading strategies

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License 