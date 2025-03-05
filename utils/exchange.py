class HyperliquidExchange:
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
        }
        self.orders = []
    
    def create_order(self,
                     asset: int,
                     isBuy: bool,
                     price: str,
                     size: str,
                     reduceOnly: bool,
                     type: str,
                     behavior: str = None,
                     cloid: str = None,):
        """
        See Python SDK for full featured examples on the fields of the order request.

        For limit orders, TIF (time-in-force) sets the behavior of the order upon first hitting the book.
            ALO (add liquidity only, i.e. "post only") will be canceled instead of immediately matching.
            IOC (immediate or cancel) will have the unfilled part canceled instead of resting.
            GTC (good til canceled) orders have no special behavior.

        Client Order ID (cloid) is an optional 128 bit hex string, e.g. 0x1234567890abcdef1234567890abcdef
        {

        "type": "order",
        "orders": [{
            "a": Number,
            "b": Boolean,
            "p": String,
            "s": String,
            "r": Boolean,
            "t": {
            "limit": {
                "tif": "Alo" | "Ioc" | "Gtc" 
            } or
            "trigger": {
                "isMarket": Boolean,
                "triggerPx": String,
                "tpsl": "tp" | "sl"
            }
            },
            "c": Cloid (optional)
        }],
        "grouping": "na" | "normalTpsl" | "positionTpsl",
        "builder": Optional({"b": "address", "f": Number})
        }
        Meaning of keys:
            a is asset
            b is isBuy
            p is price
            s is size
            r is reduceOnly
            t is type
            c is cloid (client order id)
        Meaning of keys in optional builder argument:
            b is the address the should receive the additional fee
            f is the size of the fee in tenths of a basis point e.g. if f is 10, 1bp of the order notional  will be charged to the user and sent to the builder
    """
        if type == "limit":
            if behavior is None:
                behavior = "Gtc"
            if behavior not in ["Alo", "Ioc", "Gtc"]:
                raise ValueError("Invalid TIF value")
            type_behavior = {
                "limit": {
                    "tif": behavior
                }
            }
        elif type == "trigger":
            if behavior is None:
                raise ValueError("Trigger orders require a behavior")
            if behavior not in ["tp", "sl"]:
                raise ValueError("Invalid trigger behavior")
            type_behavior = {
                "trigger": {
                    "isMarket": False,
                    "triggerPx": price,
                    "tpsl": behavior
                }
            }

        self.orders.append({
            "a": asset,
            "b": isBuy,
            "p": price,
            "s": size,
            "r": reduceOnly,
            "t": type_behavior,
            "c": cloid,
        })

    def _build_order(self,
                     asset: int,
                     isBuy: bool,
                     price: str,
                     size: str,
                     reduceOnly: bool,
                     order_type: dict,
                     cloid: str = None):
        """Helper function to build an order."""
        return {
            "a": asset,
            "b": isBuy,
            "p": price,
            "s": size,
            "r": reduceOnly,
            "t": order_type,
            "c": cloid,
        }
    
    def create_limit_order(self,
                           asset: int,
                           isBuy: bool,
                           price: str,
                           size: str,
                           reduceOnly: bool,
                           tif: str = "Gtc",
                           cloid: str = None):
        """Creates a limit order."""
        if tif not in ["Alo", "Ioc", "Gtc"]:
            raise ValueError("Invalid TIF value")
        order = self._build_order(asset, isBuy, price, size, reduceOnly, {"limit": {"tif": tif}}, cloid)
        self.orders.append(order)

    def create_market_order(self,
                            asset: int,
                            isBuy: bool,
                            size: str,
                            reduceOnly: bool,
                            cloid: str = None):
        """Creates a market order."""
        order = self._build_order(
            asset=asset,
            isBuy=isBuy,
            price="0",
            size=size,
            reduceOnly=reduceOnly,
            order_type={"market": {}},
            cloid=cloid)
        self.orders.append(order)

    