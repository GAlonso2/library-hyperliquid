from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from ..utils.constants import LIMIT, BUY, OPEN
from ..utils.helpers import generate_unique_id, current_timestamp

@dataclass
class Order:
    """Class representing an order on Hyperliquid."""
    
    symbol: str
    side: str
    order_type: str
    qty: float
    price: Optional[float] = None
    client_id: Optional[str] = None
    status: str = OPEN
    filled_qty: float = 0.0
    avg_fill_price: Optional[float] = None
    timestamp: int = 0
    order_id: Optional[str] = None
    leverage: Optional[int] = None
    reduce_only: bool = False
    time_in_force: Optional[str] = None
    post_only: bool = False
    
    def __post_init__(self):
        if not self.client_id:
            self.client_id = generate_unique_id()
        if not self.timestamp:
            self.timestamp = current_timestamp()
            
    def to_api_format(self) -> Dict[str, Any]:
        """Convert order to API format for submission."""
        order = {
            "coin": self.symbol,
            "is_buy": self.side == BUY,
            "sz": self.qty,
            "limit_px": self.price if self.order_type == LIMIT else None,
            "order_type": self.order_type,
            "cloid": self.client_id,
            "reduce_only": self.reduce_only,
        }
        
        # Remove None values
        return {k: v for k, v in order.items() if v is not None}
    
    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> 'Order':
        """Create order object from API response."""
        side = BUY if response.get("is_buy", False) else "a"
        return cls(
            symbol=response.get("coin", ""),
            side=side,
            order_type=response.get("order_type", ""),
            qty=float(response.get("sz", 0)),
            price=float(response.get("limit_px", 0)) if response.get("limit_px") else None,
            client_id=response.get("cloid", ""),
            status=response.get("status", OPEN),
            filled_qty=float(response.get("filled_sz", 0)),
            avg_fill_price=float(response.get("avg_px", 0)) if response.get("avg_px") else None,
            timestamp=response.get("timestamp", 0),
            order_id=response.get("oid", ""),
            reduce_only=response.get("reduce_only", False),
        ) 