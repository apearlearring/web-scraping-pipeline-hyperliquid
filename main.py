import asyncio
from fetch import DataFetcher
from process import DataProcessor
from config.settings import CRYPTO_NAMES
from process import (
    DataProcessor,
    process_analytics_positions,
    process_ls_trend_data
)
from validate import (
    validate_global_data,
    validate_asset_data,
    validate_liquidation_distribution_data,
    validate_ls_trend_data
)

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