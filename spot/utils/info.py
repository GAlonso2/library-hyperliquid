import aiohttp
import asyncio

class HyperSpotInfo:
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
        Retrieve spot metadata

        Returns:
            dict: Spot metadata
        """
        params = {
            "type": "spotMeta"
        }
        return await self._call(params)
    
    async def get_assets_context(self):
        """
        Retrieve spot asset contexts.

        Returns:
            list: [
                dict: Assets metadata,
                dict: Asset contexts
            ]
        """
        params = {
            "type": "spotMetaAndAssetCtxs"
        }
        return await self._call(params)
    
    async def get_account_balance(self, address: str):
        """
        Retrieve a user's token balances

        Args:
            address (str): Onchain address in 42-character hexadecimal format; e.g. 0x0000000000000000000000000000000000000000.

        Returns:
            dict: Account balances
        """
        params = {
            "type": "spotClearinghouseState",
            "user": address
        }
        return await self._call(params)
    
    async def get_account_deploy_auction(self,
                                          address: str,):
        """
        Retrieve information about the Spot Deploy Auction

        Args:
            address (str): Onchain address in 42-character hexadecimal format; e.g. 0x0000000000000000000000000000000000000000.
        """
        params = {
            "type": "spotDeployState",
            "user": address,
        }
        return await self._call(params)
    
    async def get_token_info(self,
                             token_id: str,):
        """
        Retrieve information about a Token

        Args:
            token_id (str): Onchain id in 34-character hexadecimal format; e.g. 0x00000000000000000000000000000000.
        """
        params = {
            "type": "tokenDetails",
            "tokenId": token_id,
        }
        return await self._call(params)
        
async def main():
    info = HyperSpotInfo()
    metadata = await info.get_token_info("0xbaf265ef389da684513d98d68edf4eae")#"0x84A6d1E07517e21123E8FfF5b705333577C9FdF7")
    print(metadata)

if __name__ == '__main__':
    asyncio.run(main())