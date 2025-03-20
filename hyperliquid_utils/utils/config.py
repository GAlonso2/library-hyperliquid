from typing import Dict, Any, Optional

class Config:
    """Configuration class for Hyperliquid API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        private_key: Optional[str] = None,
        use_testnet: bool = False,
        base_currency: str = "USD",
        default_leverage: int = 1,
        max_leverage: int = 20,
        default_timeout: int = 10,
        default_retry: int = 3,
    ):
        """
        Initialize configuration.
        
        Args:
            api_key: API key (optional)
            private_key: Private key for signing (optional)
            use_testnet: Whether to use testnet
            base_currency: Base currency for trading
            default_leverage: Default leverage for new positions
            max_leverage: Maximum allowed leverage
            default_timeout: Default request timeout in seconds
            default_retry: Default number of retries for failed requests
        """
        self.api_key = api_key
        self.private_key = private_key
        self.use_testnet = use_testnet
        self.base_currency = base_currency
        self.default_leverage = default_leverage
        self.max_leverage = max_leverage
        self.default_timeout = default_timeout
        self.default_retry = default_retry
        
    @property
    def api_url(self) -> str:
        from .constants import TESTNET_API_URL, MAINNET_API_URL
        return TESTNET_API_URL if self.use_testnet else MAINNET_API_URL
    
    @property
    def ws_url(self) -> str:
        from .constants import TESTNET_WS_URL, MAINNET_WS_URL
        return TESTNET_WS_URL if self.use_testnet else MAINNET_WS_URL 