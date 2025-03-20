from typing import Dict, List, Any, Optional, Union, Callable
import time
import asyncio
from ..models.order import Order
from ..models.position import Position
from ..models.market import Market
from ..utils.helpers import make_request_async
from ..utils.constants import LIMIT, MARKET, BUY, SELL

class OrderManager:
    """Async Order Management System for Hyperliquid."""
    
    def __init__(self, auth: Any, api_url: str, ws_url: str):
        """
        Initialize order manager.
        
        Args:
            auth: Authentication object
            api_url: API URL
            ws_url: Websocket URL
        """
        self.auth = auth
        self.api_url = api_url
        self.ws_url = ws_url
        self.active_orders = {}  # client_id -> Order
        self.positions = {}  # symbol -> Position
        self.markets = {}  # symbol -> Market
        self.on_order_update = None
        self.on_position_update = None
        self.on_trade_update = None
        self.on_error = None
        self._last_sync = 0
        self._sync_interval = 60  # seconds
        self._running = False
        self._sync_task = None
        
    async def start(self):
        """Start order manager asynchronously."""
        self._running = True
        await self.sync_markets()
        await self.sync_positions()
        await self.sync_orders()
        
        # Start async task for periodic syncing
        self._sync_task = asyncio.create_task(self._sync_loop())
        
    async def stop(self):
        """Stop order manager."""
        self._running = False
        
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        
    async def _sync_loop(self):
        """Background loop for periodic syncing."""
        while self._running:
            current_time = time.time()
            if current_time - self._last_sync > self._sync_interval:
                await self.sync_positions()
                await self.sync_orders()
                self._last_sync = current_time
            await asyncio.sleep(5)
            
    async def sync_markets(self) -> Dict[str, Market]:
        """Sync markets data asynchronously."""
        try:
            response = await make_request_async("GET", "/info/meta", self.api_url)
            
            if "error" in response:
                if self.on_error:
                    await self._call_callback(self.on_error, f"Error syncing markets: {response['error']}")
                return self.markets
                
            for market_data in response.get("assetInfos", []):
                market = Market.from_api_response(market_data)
                self.markets[market.symbol] = market
                
            return self.markets
        except Exception as e:
            if self.on_error:
                await self._call_callback(self.on_error, f"Error syncing markets: {e}")
            return self.markets
            
    async def sync_positions(self) -> Dict[str, Position]:
        """Sync user positions asynchronously."""
        if not self.auth:
            if self.on_error:
                await self._call_callback(self.on_error, "Authentication required to sync positions")
            return self.positions
            
        try:
            response = await make_request_async(
                "POST", 
                "/info/user/positions", 
                self.api_url,
                params={"address": self.auth.address},
                auth=self.auth
            )
            
            if "error" in response:
                if self.on_error:
                    await self._call_callback(self.on_error, f"Error syncing positions: {response['error']}")
                return self.positions
                
            position_data = response.get("positions", [])
            for pos_data in position_data:
                position = Position.from_api_response(pos_data)
                self.positions[position.symbol] = position
                
                if self.on_position_update:
                    await self._call_callback(self.on_position_update, position)
                    
            return self.positions
        except Exception as e:
            if self.on_error:
                await self._call_callback(self.on_error, f"Error syncing positions: {e}")
            return self.positions
            
    async def sync_orders(self) -> Dict[str, Order]:
        """Sync user orders asynchronously."""
        if not self.auth:
            if self.on_error:
                await self._call_callback(self.on_error, "Authentication required to sync orders")
            return self.active_orders
            
        try:
            response = await make_request_async(
                "POST", 
                "/info/user/openOrders", 
                self.api_url,
                params={"address": self.auth.address},
                auth=self.auth
            )
            
            if "error" in response:
                if self.on_error:
                    await self._call_callback(self.on_error, f"Error syncing orders: {response['error']}")
                return self.active_orders
                
            # Clear active orders to refresh
            old_orders = self.active_orders.copy()
            self.active_orders = {}
            
            orders_data = response.get("orders", [])
            for order_data in orders_data:
                order = Order.from_api_response(order_data)
                self.active_orders[order.client_id] = order
                
                if self.on_order_update:
                    await self._call_callback(self.on_order_update, order)
                    
            return self.active_orders
        except Exception as e:
            if self.on_error:
                await self._call_callback(self.on_error, f"Error syncing orders: {e}")
            return self.active_orders

    async def _call_callback(self, callback, *args, **kwargs):
        """Helper method to call callbacks with proper async/sync handling."""
        if asyncio.iscoroutinefunction(callback):
            await callback(*args, **kwargs)
        else:
            callback(*args, **kwargs)
            
    async def place_order(self, order: Order) -> Optional[Order]:
        """
        Place an order asynchronously.
        
        Args:
            order: Order to place
            
        Returns:
            Updated order or None if failed
        """
        if not self.auth:
            if self.on_error:
                await self._call_callback(self.on_error, "Authentication required to place order")
            return None
            
        try:
            payload = {
                "action": {
                    "order": order.to_api_format()
                },
                "address": self.auth.address
            }
            
            response = await make_request_async(
                "POST", 
                "/exchange/order", 
                self.api_url,
                params=payload,
                auth=self.auth
            )
            
            if "error" in response:
                if self.on_error:
                    await self._call_callback(self.on_error, f"Error placing order: {response['error']}")
                return None
                
            # Update order with response
            updated_order = Order.from_api_response(response.get("order", {}))
            self.active_orders[updated_order.client_id] = updated_order
            
            if self.on_order_update:
                await self._call_callback(self.on_order_update, updated_order)
                
            return updated_order
        except Exception as e:
            if self.on_error:
                await self._call_callback(self.on_error, f"Error placing order: {e}")
            return None
            
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order asynchronously.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if successful, False otherwise
        """
        if not self.auth:
            if self.on_error:
                await self._call_callback(self.on_error, "Authentication required to cancel order")
            return False
            
        try:
            payload = {
                "action": {
                    "cancel": {
                        "oid": order_id
                    }
                },
                "address": self.auth.address
            }
            
            response = await make_request_async(
                "POST", 
                "/exchange/cancel", 
                self.api_url,
                params=payload,
                auth=self.auth
            )
            
            if "error" in response:
                if self.on_error:
                    await self._call_callback(self.on_error, f"Error canceling order: {response['error']}")
                return False
                
            # Remove from active orders if successful
            for client_id, order in list(self.active_orders.items()):
                if order.order_id == order_id:
                    del self.active_orders[client_id]
                    break
                    
            return True
        except Exception as e:
            if self.on_error:
                await self._call_callback(self.on_error, f"Error canceling order: {e}")
            return False
            
    async def cancel_all_orders(self, symbol: Optional[str] = None) -> bool:
        """
        Cancel all orders asynchronously, optionally filtered by symbol.
        
        Args:
            symbol: Optional symbol to filter orders
            
        Returns:
            True if successful, False otherwise
        """
        if not self.auth:
            if self.on_error:
                await self._call_callback(self.on_error, "Authentication required to cancel orders")
            return False
            
        try:
            payload = {
                "action": {
                    "cancelAll": {}
                },
                "address": self.auth.address
            }
            
            if symbol:
                payload["action"]["cancelAll"]["coin"] = symbol
                
            response = await make_request_async(
                "POST", 
                "/exchange/cancelAll", 
                self.api_url,
                params=payload,
                auth=self.auth
            )
            
            if "error" in response:
                if self.on_error:
                    await self._call_callback(self.on_error, f"Error canceling orders: {response['error']}")
                return False
                
            # Clear active orders if successful
            if symbol:
                self.active_orders = {
                    client_id: order for client_id, order in self.active_orders.items() 
                    if order.symbol != symbol
                }
            else:
                self.active_orders = {}
                
            return True
        except Exception as e:
            if self.on_error:
                await self._call_callback(self.on_error, f"Error canceling orders: {e}")
            return False
            
    def get_order(self, client_id: str) -> Optional[Order]:
        """
        Get order by client ID.
        
        Args:
            client_id: Client order ID
            
        Returns:
            Order or None if not found
        """
        return self.active_orders.get(client_id)
        
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position by symbol.
        
        Args:
            symbol: Symbol
            
        Returns:
            Position or None if not found
        """
        return self.positions.get(symbol)
        
    def get_market(self, symbol: str) -> Optional[Market]:
        """
        Get market by symbol.
        
        Args:
            symbol: Symbol
            
        Returns:
            Market or None if not found
        """
        return self.markets.get(symbol) 