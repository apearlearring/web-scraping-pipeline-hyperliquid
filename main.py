import asyncio
from datetime import datetime
from typing import Dict, List, Tuple
import json

from fetch.fetch_website import fetch_website
from process.process_data import (
    process_analytics_positions,
    process_liquidation_data,
    process_ls_trend_data
)
from validate.validate import (
    validate_global_data,
    validate_asset_data,
    validate_liquidation_distribution_data,
    validate_ls_trend_data
)

# Constants
CRYPTO_NAMES = ["BTC", "ETH", "SOL"]
BASE_URLS = {
    'position': 'https://api.hyperdash.info/summary',
    'ls_trend': 'https://api.hyperdash.info/ls_trend',
    'funding_history': 'https://api.hyperliquid.xyz/info',
    'liquidation': 'https://hyperdash.info/api/liquidation-data-v2'
}
API_KEY = 'hyperdash_public_7vN3mK8pQ4wX2cL9hF5tR1bY6gS0jD'

class DataFetcher:
    def __init__(self):
        self.liquidation_headers = {'x-api-key': API_KEY}
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

class DataProcessor:
    @staticmethod
    def process_crypto_data(
        crypto_name: str,
        liquidation_data: Dict,
        funding_history: Dict,
        assets_position_data: Dict,
        ls_trend_data: List[Dict]
    ) -> Tuple[Dict, Dict, Dict]:
        """
        Processes data for a specific cryptocurrency.
        """
        liquidation_metrics, liquidation_distribution = process_liquidation_data(
            liquidation_data, crypto_name
        )

        # Find and update asset position data
        asset_position = next(
            (asset for asset in assets_position_data['data'] 
             if asset['Asset'] == crypto_name),
            None
        )
        
        if asset_position:
            asset_position.update({
                'Liquidation_Metrics': liquidation_metrics,
                'Funding_History': funding_history[-1],
                'Timestamp': assets_position_data["lastUpdated"]
            })

        # Find corresponding L/S trend data
        ls_trend = next(
            (trend for trend in ls_trend_data 
             if trend['Asset'] == crypto_name),
            None
        )

        return asset_position, liquidation_distribution, ls_trend

async def fetch_and_process_data():
    """
    Main function to fetch and process all data.
    """
    fetcher = DataFetcher()
    processor = DataProcessor()

    try:
        # Fetch global data
        assets_position_data, ls_trend_data = await fetcher.fetch_position_ls_trend_data()
        global_analytics_data = process_analytics_positions(assets_position_data)

        # Fetch crypto-specific data
        crypto_tasks = [fetcher.fetch_crypto_liquidation_funding_data(crypto) for crypto in CRYPTO_NAMES]
        crypto_results = await asyncio.gather(*crypto_tasks)

        # Process results
        processed_data = {
            'asset_positions': [],
            'liquidation_distributions': [],
            'ls_trends': []
        }

        for i, crypto_name in enumerate(CRYPTO_NAMES):
            try:
                liquidation_data, funding_history = crypto_results[i]
                
                asset_position, liquidation_distribution, ls_trend = processor.process_crypto_data(
                    crypto_name,
                    liquidation_data,
                    funding_history,
                    assets_position_data,
                    ls_trend_data
                )

                if asset_position:
                    processed_data['asset_positions'].append(asset_position)
                if liquidation_distribution:
                    processed_data['liquidation_distributions'].append(liquidation_distribution)
                if ls_trend:
                    processed_data['ls_trends'].append(ls_trend)

            except Exception as e:
                print(f"Error processing {crypto_name}: {e}")
                continue

        # Process L/S trend data
        processed_ls_trend_data = process_ls_trend_data(processed_data['ls_trends'])

        # Validate all data
        validated_data = {
            'global_analytics': validate_global_data(global_analytics_data),
            'assets': validate_asset_data(processed_data['asset_positions']),
            'liquidation_distribution': validate_liquidation_distribution_data(
                processed_data['liquidation_distributions']
            ),
            'ls_trend': validate_ls_trend_data(processed_ls_trend_data)
        }

        return validated_data

    except Exception as e:
        print(f"Error in fetch_and_process_data: {e}")
        raise

async def main():
    """
    Entry point of the application.
    """
    try:
        validated_data = await fetch_and_process_data()
        print(validated_data['assets'])
        return validated_data
    except Exception as e:
        print(f"Application error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 