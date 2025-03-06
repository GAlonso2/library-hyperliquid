import os
import asyncio

from hyperliquid.info import HyperliquidInfo
from utils.spot_info import HyperSpotInfo
from hyperliquid.utils import constants

class HyperliquidUserData(HyperliquidInfo):
    def __init__(
        self,
        order_update_function=None,
        fills_update_function=None
    ):
        self.address = os.getenv('ACCOUNT_ADDRESS')
        self.hyperliquid_spot_info = HyperSpotInfo()
        self.balance = {}
        self.orders = {}

        self.hyperliquid_stream = HyperliquidInfo(
            base_url=constants.MAINNET_API_URL,
            skip_ws=False,
            on_message_function=self.user_message
        )
        self.hyperliquid_stream.subscribe(
            subscription={
                "type": "userEvents",
                "user": self.address,
            },
            callback=self.user_message,
        )
        self.hyperliquid_stream.subscribe(
            subscription={
                "type": "userFills",
                "user": self.address,
            },
            callback=self.user_message,
        )
        self.hyperliquid_stream.subscribe(
            subscription={
                "type": "orderUpdates",
                "user": self.address,
            },
            callback=self.user_message,
        )

        if order_update_function:
            self.order_update_function = order_update_function
        else:
            self.order_update_function = self.order_updates

        if fills_update_function:
            self.fills_update_function = fills_update_function
        else:
            self.fills_update_function = self.fills_updates
    
    async def user_message(self, message):
        data = message['data']
        if message["channel"] == 'orderUpdates':
            self.order_update_function(data)
        elif message["channel"] == 'userFills':
            self.fills_update_function(data)
        print(message)

    def order_updates(self, data):
        self.order_balance_update(data)
        print(data)

    def order_balance_update(self, data):
        for order_update in data:
            if order_update['status'] == 'canceled':
                order = order_update['order']
                if order['side'] == 'B':
                    amount = float(order['limitPx']) * float(order['sz'])
                    self.balance['USDC']['free'] += amount
                    self.balance['USDC']['locked'] -= amount
                self.orders.pop(order['oid'], None)
                pass
            elif order_update['status'] == 'open':
                order = order_update['order']
                self.orders[order['oid']] = {
                    'side': order['side'],
                    'price': order['limitPx'],
                    'size': order['sz'],
                    'filled': 0
                }

        print(data)

    def fills_updates(self, data):
        print(data)

    async def fetch_balance(self):
        balances = await self.hyperliquid_spot_info.get_account_balance(
            self.address)
        
        self.balance = {}
        for balance in balances['balances']:
            self.balance[balance['coin']] = {
                'free': float(balance['total']) - \
                    float(balance['hold']),
                'locked': float(balance['hold'])
            }
    
    async def start(self):
        await self.fetch_balance()

        spot_metadata = await self.hyperliquid_spot_info.get_metadata()
        tokens = spot_metadata['tokens']
        self.tokens = {}
        for asset in spot_metadata['universe']:
            self.tokens[asset['name']] = tokens[asset['tokens'][0]]['name']

        await self.hyperliquid_stream.connect_websocket()

async def main():
    user_data = HyperliquidUserData()
    await user_data.start()

if __name__ == "__main__":
    asyncio.run(main())