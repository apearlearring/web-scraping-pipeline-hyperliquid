import asyncio
from fetch import *
from process import *
from config.settings import CRYPTO_NAMES
from validate import *
from db import *
from datetime import datetime
import logging
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
import gc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def fetch_asset_data(asset: str) -> Dict:
    """Fetch all data for a single asset concurrently"""
    try:
        liquidation_data, funding_history = await asyncio.gather(
            fetch_liquidation(asset),
            fetch_funding_history(asset)
        )
        return {
            'asset': asset,
            'liquidation_data': liquidation_data,
            'funding_history': funding_history
        }
    except Exception as e:
        logging.error(f"Error fetching data for {asset}: {e}")
        return None

async def process_asset_data(asset_data: Dict, position_data: Dict, timestamp: str) -> Dict:
    """Process data for a single asset"""
    try:
        processed_funding_history = process_funding_history(asset_data['funding_history'][-1])
        asset_position_data = next(
            (data for data in position_data['data'] if data['Asset'] == asset_data['asset']), 
            None
        )
        
        liquidation_metrics, liquidation_distribution = process_liquidation(
            liquidation_data=asset_data['liquidation_data'],
            asset_name=asset_data['asset']
        )
        
        processed_position = process_position(
            position_data=asset_position_data,
            funding_history=processed_funding_history,
            liquidation_metrics=liquidation_metrics,
            lastupdated=timestamp
        )
        
        return {
            'position': processed_position,
            'liquidation_distribution': liquidation_distribution
        }
    except Exception as e:
        logging.error(f"Error processing data for {asset_data['asset']}: {e}")
        return None

async def batch_process_assets(assets: List[str], batch_size: int = 3):
    """Process assets in batches to manage memory"""
    try:
        # Fetch common data first
        position_data = await fetch_position()
        ls_trend_data = await fetch_ls_trend()
        timestamp = position_data['lastUpdated']

        # Process global data
        global_position_data = process_global_position(position_data)
        processed_ls_trend_data = process_ls_trend(ls_trend_data)

        # Initialize InfluxDB writer
        influx_writer = InfluxWriter()
        
        # Process assets in batches
        for i in range(0, len(assets), batch_size):
            batch = assets[i:i + batch_size]
            logging.info(f"Processing batch {i//batch_size + 1}: {batch}")
            
            # Fetch data for batch concurrently
            asset_data_tasks = [fetch_asset_data(asset) for asset in batch]
            asset_data_results = await asyncio.gather(*asset_data_tasks)
            
            # Process batch data
            processed_data = []
            processed_liquidation_distribution = []
            
            for asset_data in asset_data_results:
                if asset_data:
                    result = await process_asset_data(asset_data, position_data, timestamp)
                    if result:
                        processed_data.append(result['position'])
                        processed_liquidation_distribution.append(result['liquidation_distribution'])
            
            # Validate batch data
            if processed_data:
                validated_positions = validate_position_data(processed_data)
                validated_liquidation_distribution = validate_liquidation_distribution_data(processed_liquidation_distribution)
                
                # Write batch to InfluxDB
                await write_to_influx(validated_positions, None)  # Write positions only
                
            # Clear batch data from memory
            del asset_data_results
            del processed_data
            del processed_liquidation_distribution
            gc.collect()
            
            logging.info(f"Completed batch {i//batch_size + 1}")
            
        # Process and write global data after all batches
        validated_global_position_data = validate_global_position_data(global_position_data)
        validated_ls_trend_data = validate_ls_trend_data(processed_ls_trend_data)
        
        # Write global data
        await write_to_influx(None, validated_global_position_data)
        
        logging.info("All data processing completed successfully")
        
    except Exception as e:
        logging.error(f"Error in batch processing: {e}")
        raise

async def write_to_influx(validated_position_data, validated_global_position_data):
    """Write validated data to InfluxDB"""
    try:
        influx_writer = InfluxWriter()
        
        if validated_position_data:
            influx_writer.write_position_data(validated_position_data)
            
        if validated_global_position_data:
            influx_writer.write_global_position(validated_global_position_data)
            
    except Exception as e:
        logging.error(f"Error writing to InfluxDB: {e}")
        raise
    finally:
        influx_writer.close()

async def main():
    try:
        # Configure batch size based on available memory and asset count
        BATCH_SIZE = 3  # Adjust based on your system's capabilities
        
        # Start batch processing
        await batch_process_assets(CRYPTO_NAMES, BATCH_SIZE)
        
    except Exception as e:
        logging.error(f"Application error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
    
    # Show position data (can be run separately)
    # asyncio.run(show_position_data(24))  # Show last 24 hours of data
