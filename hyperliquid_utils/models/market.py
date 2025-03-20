from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class Market:
    """Class representing a market on Hyperliquid."""
    
    symbol: str
    name: str
    base_currency: str
    quote_currency: str
    tick_size: float
    lot_size: float
    min_order_size: float
    price_precision: int
    size_precision: int
    funding_rate: float = 0.0
    mark_price: float = 0.0
    index_price: float = 0.0
    open_interest: float = 0.0
    
    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> 'Market':
        """Create market object from API response."""
        meta = response.get("meta", {})
        sz_decimals = meta.get("sz_decimals", 3)
        price_decimals = meta.get("price_decimals", 2)
        
        return cls(
            symbol=response.get("name", ""),
            name=response.get("name", ""),
            base_currency=response.get("name", ""),
            quote_currency="USD",
            tick_size=float(f"0.{'0' * (price_decimals-1)}1"),
            lot_size=float(f"0.{'0' * (sz_decimals-1)}1"),
            min_order_size=float(meta.get("min_order_size", 0)),
            price_precision=price_decimals,
            size_precision=sz_decimals,
            funding_rate=float(response.get("funding_rate", 0)),
            mark_price=float(response.get("mark_px", 0)),
            index_price=float(response.get("oracle_px", 0)),
            open_interest=float(response.get("open_interest", 0)),
        ) 