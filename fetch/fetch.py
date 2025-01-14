import json
import asyncio
from config.settings import LIQUIDATION_HEADERS, BASE_URLS
from datetime import datetime
from typing import Dict, Tuple
from fetch import fetch_website


class DataFetcher:
    def __init__(self):
        self.liquidation_headers = LIQUIDATION_HEADERS
        self.asset_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    async def fetch_crypto_liquidation_funding_data(self, crypto_name: str) -> Tuple[Dict, Dict]:
        """
        Fetches liquidation and funding data for a specific cryptocurrency.
        """
        funding_history_settings = {
            'method': 'POST',
            'body': json.dumps({
                "type": "fundingHistory",
                "coin": crypto_name,
                "startTime": int((datetime.now().timestamp() - 10800) * 1000),
                "endTime": int(datetime.now().timestamp() * 1000)
            })
        }

        liquidation_url = f"{BASE_URLS['liquidation']}?ticker={crypto_name}&days=7"

        liquidation_data, funding_history = await asyncio.gather(
            fetch_website(liquidation_url, headers=self.liquidation_headers),
            fetch_website(
                BASE_URLS['funding_history'],
                headers=self.asset_headers,
                page_settings=funding_history_settings
            )
        )
        
        return liquidation_data, funding_history

    async def fetch_position_ls_trend_data(self) -> Tuple[Dict, Dict]:
        """
        Fetches asset position and L/S trend data.
        """
        return await asyncio.gather(
            fetch_website(BASE_URLS['position']),
            fetch_website(BASE_URLS['ls_trend'])
        )
