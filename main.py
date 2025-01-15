import asyncio
from fetch import *
from process import *
from config.settings import CRYPTO_NAMES
from validate import *
from db import *
from datetime import datetime

async def write_to_influx(validated_position_data, validated_global_position_data):
    """Write validated position and global position data to InfluxDB"""
    try:
        influx_writer = InfluxWriter()
        influx_writer.write_position_data(validated_position_data)
        influx_writer.write_global_position(validated_global_position_data)
    except Exception as e:
        print(f"Error writing to InfluxDB: {e}")
        raise

async def main():

    try:
        position_data = await fetch_position()
        ls_trend_data = await fetch_ls_trend()

        processed_position_data = []
        processed_liquidation_distribution_data = []
        global_position_data = process_global_position(position_data)
        processed_ls_trend_data = process_ls_trend(ls_trend_data)

        for asset in CRYPTO_NAMES:
            liquidation_data = await fetch_liquidation(asset)
            funding_history = await fetch_funding_history(asset)

            processed_funding_history = process_funding_history(funding_history[-1])
            asset_position_data = next((data for data in position_data['data'] if data['Asset'] == asset), None)
            liquidation_metrics, liquidation_distribution = process_liquidation(liquidation_data = liquidation_data, asset_name=asset)
            asset_position_data = process_position(position_data = asset_position_data, funding_history = processed_funding_history, liquidation_metrics = liquidation_metrics, lastupdated = position_data['lastUpdated'])

            processed_position_data.append(asset_position_data)
            processed_liquidation_distribution_data.append(liquidation_distribution)
            print(asset_position_data)

        print(global_position_data)
        # Validation

        validated_position_data = validate_position_data(processed_position_data)
        validated_liquidation_distribution_data = validate_liquidation_distribution_data(processed_liquidation_distribution_data)
        validated_global_position_data = validate_global_position_data(global_position_data)
        validated_ls_trend_data = validate_ls_trend_data(processed_ls_trend_data)

        # Write validated data to InfluxDB
        await write_to_influx(validated_position_data, validated_global_position_data)

    except Exception as e:
        print(f"Application error: {e}")
        raise

if __name__ == "__main__":
    # Run main data collection
    asyncio.run(main())
    
    # Show position data (can be run separately)
    # asyncio.run(show_position_data(24))  # Show last 24 hours of data
