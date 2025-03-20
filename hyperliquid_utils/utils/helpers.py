import time
import hmac
import hashlib
import json
import uuid
from typing import Dict, List, Any, Optional, Union
import aiohttp
from .constants import MAINNET_API_URL

def generate_unique_id() -> str:
    """Generate a unique client order ID."""
    return str(uuid.uuid4())

def current_timestamp() -> int:
    """Get current timestamp in milliseconds."""
    return int(time.time() * 1000)

async def make_request_async(
    method: str, 
    endpoint: str, 
    api_url: str = MAINNET_API_URL, 
    params: Optional[Dict] = None, 
    auth: Optional[Any] = None
) -> Dict:
    """
    Make an async HTTP request to the Hyperliquid API.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint
        api_url: Base API URL (mainnet by default)
        params: Request parameters
        auth: Authentication object
    
    Returns:
        API response as dictionary
    """
    url = f"{api_url}{endpoint}"
    headers = {}
    
    if auth and method.upper() == "POST":
        # Handle authentication for POST requests
        headers.update(auth.get_auth_headers(endpoint, params))
    
    try:
        async with aiohttp.ClientSession() as session:
            if method.upper() == "GET":
                async with session.get(url, params=params, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
            elif method.upper() == "POST":
                async with session.post(url, json=params, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
    except aiohttp.ClientError as e:
        print(f"Request error: {e}")
        return {"error": str(e)}

# Keep the synchronous version for backward compatibility
def make_request(
    method: str, 
    endpoint: str, 
    api_url: str = MAINNET_API_URL, 
    params: Optional[Dict] = None, 
    auth: Optional[Any] = None
) -> Dict:
    """
    Make a synchronous HTTP request to the Hyperliquid API.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint
        api_url: Base API URL (mainnet by default)
        params: Request parameters
        auth: Authentication object
    
    Returns:
        API response as dictionary
    """
    import requests  # Import here to avoid dependency if using async only
    url = f"{api_url}{endpoint}"
    headers = {}
    
    if auth and method.upper() == "POST":
        # Handle authentication for POST requests
        headers.update(auth.get_auth_headers(endpoint, params))
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=params, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return {"error": str(e)}

def format_price_qty(price: float, qty: float, market_info: Dict) -> Dict:
    """
    Format price and quantity according to market specification.
    
    Args:
        price: Order price
        qty: Order quantity
        market_info: Market information including tick and lot size
    
    Returns:
        Formatted price and quantity
    """
    tick_size = market_info.get("tickSize", 0.01)
    lot_size = market_info.get("lotSize", 0.001)
    
    formatted_price = round(price / tick_size) * tick_size
    formatted_qty = round(qty / lot_size) * lot_size
    
    return {
        "price": formatted_price,
        "qty": formatted_qty
    } 