from typing import Dict, List, Any, Callable, Optional
import asyncio
from .websocket_client import HyperliquidWebsocketClient
from ..utils.constants import (
    MAINNET_WS_URL, CHANNEL_TRADES, CHANNEL_L2_BOOK, 
    CHANNEL_USER_EVENTS, CHANNEL_CANDLES, CHANNEL_TICKER
)

class StreamManager:
    """Manage multiple websocket data streams asynchronously."""
    
    def __init__(self, ws_url: str = MAINNET_WS_URL, auth: Optional[Any] = None):
        """
        Initialize stream manager.
        
        Args:
            ws_url: Websocket URL
            auth: Authentication object
        """
        self.ws_client = HyperliquidWebsocketClient(ws_url, self._on_message)
        self.auth = auth
        self.callbacks = {
            CHANNEL_TRADES: [],
            CHANNEL_L2_BOOK: [],
            CHANNEL_USER_EVENTS: [],
            CHANNEL_CANDLES: [],
            CHANNEL_TICKER: [],
        }
        
    async def _on_message(self, data: Dict[str, Any]):
        """Handle incoming messages from websocket."""
        # Determine channel from message structure
        channel = None
        if "channel" in data:
            channel = data["channel"]
        elif "type" in data:
            # Map message type to channel
            type_to_channel = {
                "trade": CHANNEL_TRADES,
                "l2Book": CHANNEL_L2_BOOK,
                "userEvent": CHANNEL_USER_EVENTS,
                "candle": CHANNEL_CANDLES,
                "ticker": CHANNEL_TICKER,
            }
            channel = type_to_channel.get(data["type"])
            
        if channel and channel in self.callbacks:
            for callback in self.callbacks[channel]:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
                
    async def connect(self):
        """Establish websocket connection."""
        await self.ws_client.connect()
        
    async def subscribe_trades(self, symbols: List[str], callback: Callable):
        """Subscribe to trade updates."""
        self.callbacks[CHANNEL_TRADES].append(callback)
        return await self.ws_client.subscribe(CHANNEL_TRADES, symbols)
        
    async def subscribe_orderbook(self, symbols: List[str], callback: Callable, depth: int = 10):
        """Subscribe to orderbook updates."""
        self.callbacks[CHANNEL_L2_BOOK].append(callback)
        return await self.ws_client.subscribe(CHANNEL_L2_BOOK, symbols, depth=depth)
        
    async def subscribe_user_events(self, callback: Callable):
        """Subscribe to user events (requires authentication)."""
        if not self.auth:
            print("Authentication required for user events subscription")
            return False
            
        self.callbacks[CHANNEL_USER_EVENTS].append(callback)
        return await self.ws_client.subscribe(CHANNEL_USER_EVENTS, auth=self.auth)
        
    async def subscribe_candles(self, symbols: List[str], callback: Callable, interval: str = "1m"):
        """Subscribe to candle updates."""
        self.callbacks[CHANNEL_CANDLES].append(callback)
        return await self.ws_client.subscribe(CHANNEL_CANDLES, symbols, interval=interval)
        
    async def subscribe_ticker(self, symbols: List[str], callback: Callable):
        """Subscribe to ticker updates."""
        self.callbacks[CHANNEL_TICKER].append(callback)
        return await self.ws_client.subscribe(CHANNEL_TICKER, symbols)
        
    async def unsubscribe_all(self):
        """Unsubscribe from all channels."""
        for channel in self.callbacks:
            await self.ws_client.unsubscribe(channel)
        self.callbacks = {channel: [] for channel in self.callbacks}
        
    async def close(self):
        """Close all connections."""
        await self.ws_client.close() 