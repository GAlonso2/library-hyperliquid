import json
import asyncio
import time
import websockets
from typing import Dict, List, Any, Callable, Optional, Union
from ..utils.constants import MAINNET_WS_URL

class HyperliquidWebsocketClient:
    """Async websocket client for Hyperliquid."""
    
    def __init__(self, ws_url: str = MAINNET_WS_URL, on_message: Optional[Callable] = None):
        """
        Initialize websocket client.
        
        Args:
            ws_url: Websocket URL
            on_message: Callback for incoming messages
        """
        self.ws_url = ws_url
        self.on_message = on_message
        self.ws = None
        self.connected = False
        self.subscriptions = set()
        self.auth = None
        self.reconnect_count = 0
        self.max_reconnect = 5
        self.last_ping = 0
        self.ping_interval = 30  # seconds
        self.loop = None
        self.task = None
        self._ping_task = None
        
    async def connect(self):
        """Establish websocket connection asynchronously."""
        try:
            self.ws = await websockets.connect(self.ws_url)
            self.connected = True
            self.reconnect_count = 0
            print("Websocket connection established")
            self.last_ping = time.time()
            
            # Start ping task to keep connection alive
            self._ping_task = asyncio.create_task(self._keep_alive())
            
            # Start message processing task
            self.task = asyncio.create_task(self._process_messages())
            
            return True
        except Exception as e:
            print(f"Websocket connection error: {e}")
            self.connected = False
            await self._reconnect()
            return False
            
    async def _process_messages(self):
        """Process incoming websocket messages."""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    if self.on_message:
                        if asyncio.iscoroutinefunction(self.on_message):
                            await self.on_message(data)
                        else:
                            self.on_message(data)
                except json.JSONDecodeError:
                    print(f"Failed to decode message: {message}")
        except websockets.exceptions.ConnectionClosed:
            print("Websocket connection closed")
            self.connected = False
            await self._reconnect()
        except Exception as e:
            print(f"Error processing messages: {e}")
            self.connected = False
            await self._reconnect()
            
    async def _reconnect(self):
        """Attempt to reconnect to websocket."""
        if self.reconnect_count < self.max_reconnect:
            self.reconnect_count += 1
            await asyncio.sleep(self.reconnect_count)  # Exponential backoff
            print(f"Attempting to reconnect... ({self.reconnect_count}/{self.max_reconnect})")
            
            if await self.connect():
                # Resubscribe to all channels
                for subscription in self.subscriptions:
                    await self.subscribe(**dict(subscription))
        else:
            print("Max reconnect attempts reached. Please reconnect manually.")
            
    async def _keep_alive(self):
        """Send periodic pings to keep connection alive."""
        while self.connected:
            if time.time() - self.last_ping > self.ping_interval:
                try:
                    if self.ws and self.connected:
                        await self.ws.send(json.dumps({"op": "ping"}))
                        self.last_ping = time.time()
                except Exception as e:
                    print(f"Ping error: {e}")
                    self.connected = False
                    await self._reconnect()
            await asyncio.sleep(5)
            
    async def subscribe(self, channel: str, symbols: List[str] = None, **kwargs):
        """Subscribe to a websocket channel."""
        if not self.connected:
            print("Websocket not connected. Connecting...")
            if not await self.connect():
                print("Failed to connect to websocket")
                return False
                
        subscription = {
            "op": "subscribe",
            "channel": channel,
        }
        
        if symbols:
            subscription["symbols"] = symbols
            
        # Add any additional parameters
        for key, value in kwargs.items():
            subscription[key] = value
            
        # Save subscription for reconnection
        self.subscriptions.add(tuple(subscription.items()))
        
        try:
            await self.ws.send(json.dumps(subscription))
            return True
        except Exception as e:
            print(f"Subscribe error: {e}")
            self.connected = False
            await self._reconnect()
            return False
            
    async def unsubscribe(self, channel: str, symbols: List[str] = None):
        """Unsubscribe from a websocket channel."""
        if not self.connected:
            return False
            
        unsubscription = {
            "op": "unsubscribe",
            "channel": channel,
        }
        
        if symbols:
            unsubscription["symbols"] = symbols
            
        # Remove from saved subscriptions
        for subscription in list(self.subscriptions):
            sub_dict = dict(subscription)
            if sub_dict.get("channel") == channel and sub_dict.get("symbols") == symbols:
                self.subscriptions.remove(subscription)
        
        try:
            await self.ws.send(json.dumps(unsubscription))
            return True
        except Exception as e:
            print(f"Unsubscribe error: {e}")
            self.connected = False
            await self._reconnect()
            return False
            
    async def close(self):
        """Close websocket connection."""
        if self.ws:
            if self._ping_task:
                self._ping_task.cancel()
                try:
                    await self._ping_task
                except asyncio.CancelledError:
                    pass
                    
            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
                    
            await self.ws.close()
            self.connected = False 