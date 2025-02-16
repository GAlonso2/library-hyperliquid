import aiohttp
import asyncio

class HyperPerpetualInfo:
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
        }

    async def _call(self, params):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url = 'https://api.hyperliquid.xyz/info',
                headers=self.headers,
                json=params) as response:
                if response.headers['Content-Type'] == 'application/json':
                    return await response.json()
                else:
                    return await response.text()
    
    async def get_metadata(self):
        """
        Retrieve perpetuals metadata

        Returns:
            dict: Perpetuals metadata
        """
        params = {
            "type": "meta"
        }
        return await self._call(params)
    
    async def get_assets_context(self):
        """
        Retrieve perpetuals asset contexts (includes mark price, current funding, open interest, etc)

        Returns:
            list: [
                dict: Assets metadata,
                dict: Asset contexts
            ]
        """
        params = {
            "type": "metaAndAssetCtxs"
        }
        return await self._call(params)
    
    async def get_account_summary(self, address: str):
        """
        See a user's open positions and margin summary for perpetuals trading.

        Args:
            address (str): Onchain address in 42-character hexadecimal format; e.g. 0x0000000000000000000000000000000000000000.

        Returns:
            dict: Account summary
        """
        params = {
            "type": "clearinghouseState",
            "user": address
        }
        return await self._call(params)
    
    async def get_account_funding_history(self,
                                          address: str,
                                          start_time: int,
                                          end_time: int=None):
        """
        Retrieve a user's funding history or non-funding ledger updates.

        Args:
            address (str): Onchain address in 42-character hexadecimal format; e.g. 0x0000000000000000000000000000000000000000.
            start_time (int): Start time in milliseconds.
            end_time (int): End time in milliseconds, defaults to current time.
        """
        params = {
            "type": "userFunding",
            "user": address,
            "startTime": start_time,
        }
        if end_time:
            params["endTime"] = end_time
        return await self._call(params)
    
    async def get_historical_funding_rates(self,
                                           coin: str,
                                           start_time: int,
                                           end_time: int=None):
        """
        Retrieve historical funding rates.

        Args:
            coin (str): Coin symbol.
            start_time (int): Start time in milliseconds.
            end_time (int): End time in milliseconds, defaults to current time.
        """
        params = {
            "type": "fundingHistory",
            "coin": coin,
            "startTime": start_time
        }
        if end_time:
            params["endTime"] = end_time
        return await self._call(params)
    
    async def get_predicted_funding_rates(self):
        """
        Retrieve predicted funding rates for different venues.

        Returns:
            dict: Predicted funding rates
        """
        params = {
            "type": "predictedFundings"
        }
        return await self._call(params)
    
    async def get_assets_at_OI_cap(self):
        """
        Query perps at open interest caps

        Returns:
            dict: Assets at open interest cap
        """
        params = {
            "type": "perpsAtOpenInterestCap"
        }
        return await self._call(params)
        
async def main():
    info = HyperPerpetualInfo()
    metadata = await info.get_assets_at_OI_cap()
    print(metadata)

if __name__ == '__main__':
    asyncio.run(main())