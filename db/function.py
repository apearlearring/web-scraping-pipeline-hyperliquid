import logging
from typing import List, Dict, Optional
from db import *

async def write_to_influx(validated_position_data: Optional[List], validated_global_position_data: Optional[Dict]) -> None:
    """Write validated data to InfluxDB with improved error handling"""
    influx_writer = None
    try:
        influx_writer = InfluxWriter()
        
        if validated_position_data:
            for position in validated_position_data:
                try:
                    influx_writer.write_position_data([position])
                except Exception as e:
                    logging.error(f"Error writing position data for {position.asset}: {e}")
                    continue
            
        if validated_global_position_data:
            try:
                influx_writer.write_global_position(validated_global_position_data)
            except Exception as e:
                logging.error(f"Error writing global position data: {e}")
        
    except Exception as e:
        logging.error(f"Error writing to InfluxDB: {e}")
        raise
    finally:
        if influx_writer:
            influx_writer.close()