import time
import json
import base64
import hashlib
from typing import Dict, Any, Optional
from eth_account import Account
from eth_account.messages import encode_defunct

class HyperliquidAuth:
    """Authentication class for Hyperliquid API."""
    
    def __init__(self, private_key: str, use_testnet: bool = False):
        """
        Initialize with private key.
        
        Args:
            private_key: Ethereum private key
            use_testnet: Whether to use testnet
        """
        self.private_key = private_key
        self.account = Account.from_key(private_key)
        self.address = self.account.address
        self.use_testnet = use_testnet
        
    def sign_message(self, message: str) -> str:
        """
        Sign a message with the private key.
        
        Args:
            message: Message to sign
            
        Returns:
            Signature as a hex string
        """
        message_hash = encode_defunct(text=message)
        signed_message = self.account.sign_message(message_hash)
        return signed_message.signature.hex()
    
    def get_auth_headers(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Args:
            endpoint: API endpoint
            payload: Request payload
            
        Returns:
            Headers with authentication
        """
        timestamp = int(time.time() * 1000)
        nonce = timestamp  # Using timestamp as nonce
        
        payload_str = json.dumps(payload, separators=(',', ':'))
        message = f"{endpoint}:{timestamp}:{nonce}:{payload_str}"
        
        signature = self.sign_message(message)
        
        return {
            "X-HL-Signature": signature,
            "X-HL-Timestamp": str(timestamp),
            "X-HL-Nonce": str(nonce),
            "X-HL-Address": self.address,
        } 