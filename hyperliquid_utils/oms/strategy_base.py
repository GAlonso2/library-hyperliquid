from typing import Dict, List, Any, Optional, Union, Callable
import time
import asyncio
from abc import ABC, abstractmethod
from ..models.order import Order
from ..models.position import Position
from ..models.market import Market
from ..utils.constants import BUY, SELL, LIMIT, MARKET
from .order_manager import OrderManager
from .position_manager import PositionManager

class Strategy(ABC):
    """Base class for async trading strategies."""
    
    def __init__(
        self, 
        order_manager: OrderManager,
        symbols: List[str],
        params: Dict[str, Any] = None
    ):
        """
        Initialize strategy.
        
        Args:
            order_manager: Order manager instance
            symbols: List of symbols to trade
            params: Strategy parameters
        """
        self.order_manager = order_manager
        self.position_manager = PositionManager(order_manager)
        self.symbols = symbols
        self.params = params or {}
        self.running = False
        self.task = None
        self.stop_event = asyncio.Event()
        
        # Register callbacks
        self.order_manager.on_order_update = self.on_order_update
        self.order_manager.on_position_update = self.on_position_update
        self.order_manager.on_trade_update = self.on_trade_update
        self.order_manager.on_error = self.on_error
        
    async def start(self):
        """Start strategy asynchronously."""
        if self.running:
            return
            
        self.running = True
        self.stop_event.clear()
        
        # Start order manager if not already running
        if not self.order_manager._running:
            await self.order_manager.start()
            
        # Initialize strategy
        await self.initialize()
        
        # Start strategy task
        self.task = asyncio.create_task(self._run_loop())
        
    async def stop(self):
        """Stop strategy asynchronously."""
        if not self.running:
            return
            
        self.running = False
        self.stop_event.set()
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            
        # Cleanup
        await self.cleanup()
        
    async def _run_loop(self):
        """Main strategy loop."""
        while self.running and not self.stop_event.is_set():
            try:
                # Run strategy iteration
                await self.on_tick()
                
                # Sleep to avoid excessive CPU usage
                await asyncio.sleep(self.params.get("tick_interval", 1))
            except Exception as e:
                await self.on_error(f"Strategy error: {e}")
                
    @abstractmethod
    async def initialize(self):
        """Initialize strategy. Override in subclass."""
        pass
        
    @abstractmethod
    async def on_tick(self):
        """
        Called on each tick of the strategy.
        Override in subclass.
        """
        pass
        
    async def cleanup(self):
        """Cleanup strategy. Override in subclass if needed."""
        pass
        
    async def on_order_update(self, order: Order):
        """
        Called when an order is updated.
        Override in subclass if needed.
        """
        pass
        
    async def on_position_update(self, position: Position):
        """
        Called when a position is updated.
        Override in subclass if needed.
        """
        pass
        
    async def on_trade_update(self, trade: Dict[str, Any]):
        """
        Called when a trade occurs.
        Override in subclass if needed.
        """
        pass
        
    async def on_error(self, error: str):
        """
        Called when an error occurs.
        Override in subclass if needed.
        """
        print(f"Strategy error: {error}")
        
    # Helper methods for strategy implementation
    
    async def buy(
        self, 
        symbol: str, 
        qty: float, 
        price: Optional[float] = None, 
        order_type: str = LIMIT
    ) -> Optional[Order]:
        """
        Place a buy order asynchronously.
        
        Args:
            symbol: Symbol
            qty: Quantity
            price: Price (required for limit orders)
            order_type: Order type (LIMIT or MARKET)
            
        Returns:
            Placed order or None if failed
        """
        return await self.position_manager.open_position(
            symbol=symbol,
            side=BUY,
            qty=qty,
            price=price,
            order_type=order_type
        )
        
    async def sell(
        self, 
        symbol: str, 
        qty: float, 
        price: Optional[float] = None, 
        order_type: str = LIMIT
    ) -> Optional[Order]:
        """
        Place a sell order asynchronously.
        
        Args:
            symbol: Symbol
            qty: Quantity
            price: Price (required for limit orders)
            order_type: Order type (LIMIT or MARKET)
            
        Returns:
            Placed order or None if failed
        """
        return await self.position_manager.open_position(
            symbol=symbol,
            side=SELL,
            qty=qty,
            price=price,
            order_type=order_type
        )
        
    async def close_all_positions(self):
        """Close all open positions asynchronously."""
        positions = self.position_manager.get_all_positions()
        close_tasks = []
        for symbol, position in positions.items():
            if position.size != 0:
                close_tasks.append(self.position_manager.close_position(symbol))
        if close_tasks:
            await asyncio.gather(*close_tasks)
                
    async def cancel_all_orders(self):
        """Cancel all open orders asynchronously."""
        await self.order_manager.cancel_all_orders() 