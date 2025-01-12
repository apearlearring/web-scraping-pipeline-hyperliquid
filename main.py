import asyncio
from fetch.fetch_website import fetch_website
from process.process_data import process_analytics_positions, process_liquidation_data
from validate.validate import validate_global_data, validate_asset_data
import json

# CRYPTO_NAMES = [
#     "BTC", "ETH", "ENA", "SOL", "LTC", "AAVE", "MKR", "WLD", "UNI", "BADGER",
#     "ILV", "XAI", "HBAR", "POPCAT", "EIGEN", "IO", "GOAT", "MOODENG", "MOVE",
#     "VIRTUAL", "FARTCOIN", "kPEPE", "XRP", "kBONK", "PNUT", "CHILLGUY", "HYPE",
#     "ME", "PURR", "DYDX", "OP", "ARB", "LINK", "AI16Z", "USUAL", "DOGE", "SUI",
#     "SEI", "TIA", "WIF", "TAO", "GRASS", "AVAX", "CRV", "APT", "FXS", "RUNE",
#     "DOT", "BIGTIME", "ORBS", "MINA", "POLYX", "GAS", "STG", "FET", "SUSHI",
#     "SUPER", "kLUNC", "RSR", "NTRN", "ACE", "MAV", "CAKE", "PEOPLE", "MANTA",
#     "UMA", "MAVIA", "PIXEL", "AI", "MYRO", "BOME", "MNT", "TNSR", "SAGA", "MERL",
#     "OMNI", "NOT", "LISTA", "kDOGS", "POL", "CATI", "CELO", "HMSTR", "NEIROETH",
#     "SAND", "IOTA", "ALGO", "HPOS"
# ]

CRYPTO_NAMES = ["BTC", "ETH", "SOL"]

async def fetch_and_process_data():
    """
    Fetches and processes analytics, asset funding history, and liquidation data.
    """
    # URLs and headers
    position_url = 'https://api.hyperdash.info/summary'
    ls_trend_url = 'https://api.hyperdash.info/ls_trend'
    asset_funding_history_url = 'https://api.hyperliquid.xyz/info'

    liquidation_headers = {'x-api-key': 'hyperdash_public_7vN3mK8pQ4wX2cL9hF5tR1bY6gS0jD'}

    # Prepare liquidation tasks
    liquidation_tasks = []
    for crypto_name in CRYPTO_NAMES:
        asset_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

        # Prepare funding history settings
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

        liquidation_tasks.extend([
            fetch_website(liquidation_data_url, headers=liquidation_headers),
            fetch_website(asset_funding_history_url, headers=asset_headers, page_settings=funding_history_page_settings)
        ])

    # Fetch all data concurrently
    results = await asyncio.gather(
        # Analytics data
        fetch_website(position_url),
        fetch_website(ls_trend_url),
        # Liquidation and funding data
        *liquidation_tasks
    )

    # Process analytics data
    assets_position_data, ls_trend_data = results[0], results[1]
    global_analytics_data = process_analytics_positions(assets_position_data)

    # Process liquidation and funding data
    processed_asset_position_data = []
    processed_ls_trend_data = []


    for i, crypto_name in enumerate(CRYPTO_NAMES):
        try:
            liquidation_data = results[2 + i * 2]
            liquidation_metrics = process_liquidation_data(liquidation_data)
            
            funding_history = results[2 + i * 2 + 1]
            
            # Find and update the corresponding asset data
            for asset in assets_position_data['data']:
                if asset['Asset'] == crypto_name:
                    asset['Liquidation_Metrics'] = liquidation_metrics
                    asset['Funding_History'] = funding_history
                    asset['Timestamp'] = assets_position_data["lastUpdated"]
                    processed_asset_position_data.append(asset)
                    break
            # Find and update the corresponding ls trend data
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
    await asyncio.gather(
        fetch_and_process_data()
    )

if __name__ == "__main__":
    asyncio.run(main()) 