from typing import Dict, Any, Optional, List, Callable
from ..models.position import Position
from ..models.order import Order
from ..utils.constants import BUY, SELL, LIMIT, MARKET
from .order_manager import OrderManager

class PositionManager:
    """Async position manager for Hyperliquid."""
    
    def __init__(self, order_manager: OrderManager):
        """
        Initialize position manager.
        
        Args:
            order_manager: Order manager instance
        """
        self.order_manager = order_manager
        
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for symbol.
        
        Args:
            symbol: Symbol
            
        Returns:
            Position or None if not found
        """
        return self.order_manager.get_position(symbol)
        
    def get_all_positions(self) -> Dict[str, Position]:
        """
        Get all positions.
        
        Returns:
            Dictionary of positions by symbol
        """
        return self.order_manager.positions
        
    async def open_position(
        self, 
        symbol: str, 
        side: str, 
        qty: float, 
        price: Optional[float] = None, 
        order_type: str = LIMIT,
        leverage: int = None,
        reduce_only: bool = False
    ) -> Optional[Order]:
        """
        Open a new position asynchronously.
        
        Args:
            symbol: Symbol
            side: BUY or SELL
            qty: Quantity
            price: Price (required for limit orders)
            order_type: Order type (LIMIT or MARKET)
            leverage: Leverage to use
            reduce_only: Whether order is reduce-only
            
        Returns:
            Placed order or None if failed
        """
        # Create order object
        order = Order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            qty=qty,
            price=price,
            leverage=leverage,
            reduce_only=reduce_only
        )
        
        # Place order asynchronously
        return await self.order_manager.place_order(order)
        
    async def close_position(
        self, 
        symbol: str, 
        price: Optional[float] = None,
        order_type: str = MARKET,
        percent: float = 100.0
    ) -> Optional[Order]:
        """
        Close an existing position asynchronously.
        
        Args:
            symbol: Symbol
            price: Price (required for limit orders)
            order_type: Order type (LIMIT or MARKET)
            percent: Percentage of position to close (0-100)
            
        Returns:
            Placed order or None if failed
        """
        position = self.get_position(symbol)
        if not position or position.size == 0:
            return None
            
        # Calculate quantity to close
        qty = abs(position.size) * (percent / 100.0)
        
        # Determine side (opposite of position)
        side = SELL if position.side == "long" else BUY
        
        # Create order
        order = Order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            qty=qty,
            price=price,
            reduce_only=True
        )
        
        # Place order asynchronously
        return await self.order_manager.place_order(order)
        
    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """
        Set leverage for a symbol asynchronously.
        
        Args:
            symbol: Symbol
            leverage: Leverage value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                "action": {
                    "updateLeverage": {
                        "coin": symbol,
                        "leverage": leverage
                    }
                },
                "address": self.order_manager.auth.address
            }
            
            response = await self.order_manager.make_request_async(
                "POST", 
                "/exchange/updateLeverage", 
                self.order_manager.api_url,
                params=payload,
                auth=self.order_manager.auth
            )
            
            if "error" in response:
                if self.order_manager.on_error:
                    await self.order_manager._call_callback(
                        self.order_manager.on_error, 
                        f"Error setting leverage: {response['error']}"
                    )
                return False
                
            return True
        except Exception as e:
            if self.order_manager.on_error:
                await self.order_manager._call_callback(
                    self.order_manager.on_error, 
                    f"Error setting leverage: {e}"
                )
            return False 