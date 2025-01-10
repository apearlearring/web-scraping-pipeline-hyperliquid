import asyncio
from fetch.fetch_website import fetch_website
from process.process_data import process_analytics_positions, process_liquidation_data, process_candle_data
import json

CRYPTO_NAMES = ["BTC"]

async def fetch_analytics():
    """
    Fetches analytics data and processes it.
    """
    position_url = 'https://api.hyperdash.info/summary'
    ls_trend_url = 'https://api.hyperdash.info/ls_trend'

    await asyncio.gather(
        fetch_website(position_url, 'position_data.json'),
        fetch_website(ls_trend_url, 'ls_trend_data.json')
    )
    process_analytics_positions('position_data.json', 'processes_analytics_data.json')

async def fetch_liquidation():
    """
    Fetches liquidation data for each cryptocurrency and processes it.
    """
    headers = {'x-api-key': 'hyperdash_public_7vN3mK8pQ4wX2cL9hF5tR1bY6gS0jD'}
    for crypto_name in CRYPTO_NAMES:
        try:
            featured_liquidation_url = f'https://hyperdash.info/api/featured-liquidations?ticker={crypto_name}'
            liquidation_data_url = f"https://hyperdash.info/api/liquidation-data-v2?ticker={crypto_name}&days=7"
            candle_data_url = f"https://hyperdash.info/api/candle-data?ticker={crypto_name}&days=1"

            await asyncio.gather(
                fetch_website(featured_liquidation_url, f'featured_liquidation_{crypto_name}.json'),
                fetch_website(liquidation_data_url, f'liquidation_data_{crypto_name}.json', headers=headers),
                fetch_website(candle_data_url, f'candle_data_{crypto_name}.json')
            )
            
            process_liquidation_data(f'liquidation_data_{crypto_name}.json', f'liquidation_summary_{crypto_name}.json')
            process_candle_data(f'candle_data_{crypto_name}.json', f'processed_candle_data_{crypto_name}.json')
            
        except Exception as e:
            print(f"Error processing {crypto_name}: {e}")

async def fetch_asset():
    """
    Fetches asset funding history data.
    """
    asset_funding_history_url = 'https://api.hyperliquid.xyz/info'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    
    funding_history_page_settings = {
        'method': 'POST',
        'body': json.dumps({
            "type": "fundingHistory",
            "coin": "BTC",
            "startTime": 1735904056588,
            "endTime": 1736508856588
        })
    }
    
    await fetch_website(asset_funding_history_url, 'BTC_funding_history.json', headers=headers, page_settings=funding_history_page_settings)

async def main():
    """
    Main function to run all fetch and process tasks.
    """
    await asyncio.gather(
        fetch_analytics(),
        fetch_liquidation(),
        fetch_asset()
    )

if __name__ == "__main__":
    asyncio.run(main()) 