from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Position:
    """Class representing a position on Hyperliquid."""
    
    symbol: str
    size: float = 0.0
    entry_price: float = 0.0
    mark_price: float = 0.0
    liquidation_price: Optional[float] = None
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    leverage: int = 1
    margin: float = 0.0
    
    @property
    def side(self) -> str:
        """Get position side (long, short, or none)."""
        if self.size > 0:
            return "long"
        elif self.size < 0:
            return "short"
        else:
            return "none"
    
    @property
    def notional_value(self) -> float:
        """Get notional value of position."""
        return abs(self.size) * self.mark_price
    
    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> 'Position':
        """Create position object from API response."""
        return cls(
            symbol=response.get("coin", ""),
            size=float(response.get("szi", 0)),
            entry_price=float(response.get("entry_px", 0)),
            mark_price=float(response.get("mark_px", 0)),
            liquidation_price=float(response.get("liq_px", 0)) if response.get("liq_px") else None,
            unrealized_pnl=float(response.get("upnl", 0)),
            realized_pnl=float(response.get("rpnl", 0)),
            margin=float(response.get("margin", 0)),
        ) 