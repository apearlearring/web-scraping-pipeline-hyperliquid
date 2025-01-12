import asyncio
from fetch.fetch_website import fetch_website
from process.process_data import process_analytics_positions, process_liquidation_data
from validate.validate import validate_global_data, validate_asset_data
import json

CRYPTO_NAMES = ["BTC", "ETH", "SOL"]

async def fetch_data_for_crypto(crypto_name, liquidation_headers, asset_funding_history_url):
    """
    Fetches liquidation and funding history data for a given cryptocurrency.

    Args:
        crypto_name (str): The name of the cryptocurrency.
        liquidation_headers (dict): Headers for the liquidation data request.
        asset_funding_history_url (str): URL for fetching asset funding history.

    Returns:
        tuple: Liquidation data and funding history data.
    """
    asset_headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

    funding_history_page_settings = {
        'method': 'POST',
        'body': json.dumps({
            "type": "fundingHistory",
            "coin": crypto_name,
            "startTime": 1735904056588,
            "endTime": 1736508856588
        })
    }

    liquidation_data_url = f"https://hyperdash.info/api/liquidation-data-v2?ticker={crypto_name}&days=7"

    liquidation_data, funding_history = await asyncio.gather(
        fetch_website(liquidation_data_url, headers=liquidation_headers),
        fetch_website(asset_funding_history_url, headers=asset_headers, page_settings=funding_history_page_settings)
    )

    return liquidation_data, funding_history

async def fetch_and_process_data():
    """
    Fetches and processes analytics, asset funding history, and liquidation data.
    """
    position_url = 'https://api.hyperdash.info/summary'
    ls_trend_url = 'https://api.hyperdash.info/ls_trend'
    asset_funding_history_url = 'https://api.hyperliquid.xyz/info'

    liquidation_headers = {'x-api-key': 'hyperdash_public_7vN3mK8pQ4wX2cL9hF5tR1bY6gS0jD'}

    # Fetch analytics data
    assets_position_data, ls_trend_data = await asyncio.gather(
        fetch_website(position_url),
        fetch_website(ls_trend_url)
    )

    # Process analytics data
    global_analytics_data = process_analytics_positions(assets_position_data)

    # Fetch and process liquidation and funding data for each crypto
    tasks = [fetch_data_for_crypto(crypto_name, liquidation_headers, asset_funding_history_url) for crypto_name in CRYPTO_NAMES]
    results = await asyncio.gather(*tasks)

    processed_asset_position_data = []
    processed_ls_trend_data = []

    for i, crypto_name in enumerate(CRYPTO_NAMES):
        try:
            liquidation_data, funding_history = results[i]
            liquidation_metrics = process_liquidation_data(liquidation_data)

            # Update asset data
            for asset in assets_position_data['data']:
                if asset['Asset'] == crypto_name:
                    asset.update({
                        'Liquidation_Metrics': liquidation_metrics,
                        'Funding_History': funding_history,
                        'Timestamp': assets_position_data["lastUpdated"]
                    })
                    processed_asset_position_data.append(asset)
                    break

            # Update ls trend data
            for ls_trend in ls_trend_data:
                if ls_trend['Asset'] == crypto_name:
                    processed_ls_trend_data.append(ls_trend)
                    break

        except Exception as e:
            print(f"Error processing {crypto_name}: {e}")

    # Validate data
    validated_global_analytics_data = validate_global_data(global_analytics_data)
    validated_assets = validate_asset_data(processed_asset_position_data)

    print(validated_global_analytics_data)
    print(validated_assets)

async def main():
    """
    Main function to run all fetch and process tasks.
    """
    await fetch_and_process_data()

if __name__ == "__main__":
    asyncio.run(main()) 