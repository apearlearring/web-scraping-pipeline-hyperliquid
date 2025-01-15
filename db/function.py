import logging
from typing import List, Dict, Optional
from db import *
from colorama import Fore, Style

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

            print(validated_global_position_data)
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

def read_from_influx(data_type: str = 'latest_positions', 
                    asset: Optional[str] = None,
                    hours: int = 24) -> List[Dict]:
    """Read data from InfluxDB with flexible query options.
    
    Args:
        data_type (str): Type of data to read ('latest_positions', 'asset_history', 'global_metrics')
        asset (Optional[str]): Asset symbol for asset-specific queries
        hours (int): Number of hours of historical data to retrieve
        
    Returns:
        List[Dict]: Query results
    """
    reader = None
    try:
        reader = InfluxReader()
        
        if data_type == 'latest_positions':
            data = reader.get_latest_positions()
            _print_position_data(data)
            return data
            
        elif data_type == 'asset_history' and asset:
            data = reader.get_asset_history(asset, hours)
            _print_asset_history(data, asset)
            return data
            
        elif data_type == 'global_metrics':
            data = reader.get_global_metrics(hours)
            _print_global_metrics(data)
            return data
            
        else:
            logging.error(f"Invalid data type: {data_type}")
            return []
            
    except Exception as e:
        logging.error(f"Error reading from InfluxDB: {e}")
        return []
    finally:
        if reader:
            reader.close()

def _print_position_data(positions: List[Dict]) -> None:
    """Format and print position data.
    
    Args:
        positions (List[Dict]): List of position data to print
    """
    if not positions:
        print(f"{Fore.YELLOW}No position data found{Style.RESET_ALL}")
        return
        
    print(f"\n{Fore.CYAN}Latest Position Data:{Style.RESET_ALL}")
    for pos in positions:
        _print_position_entry(pos)

def _print_position_entry(pos: Dict) -> None:
    """Print a single position entry.
    
    Args:
        pos (Dict): Position data dictionary
    """
    print(f"""
        {Fore.GREEN}Asset: {pos['asset']}{Style.RESET_ALL}
        Total Notional: ${pos['total_notional']:,.2f}
        L/S Ratio: {pos['ls_ratio']:.3f}
        Current Price: ${pos['current_price']:,.2f}
        Traders: {pos['traders_long']} long, {pos['traders_short']} short
        Timestamp: {pos['timestamp']}
        {'-' * 50}""")

def _print_asset_history(history: List[Dict], asset: str) -> None:
    """Format and print asset history data.
    
    Args:
        history (List[Dict]): List of historical data points
        asset (str): Asset symbol
    """
    if not history:
        print(f"{Fore.YELLOW}No historical data found for {asset}{Style.RESET_ALL}")
        return
        
    print(f"\n{Fore.CYAN}Historical Data for {asset}:{Style.RESET_ALL}")
    for point in history:
        _print_history_point(point)

def _print_history_point(point: Dict) -> None:
    """Print a single history data point.
    
    Args:
        point (Dict): Historical data point dictionary
    """
    print(f"""
        {Fore.GREEN}Timestamp: {point['timestamp']}{Style.RESET_ALL}
        Total Notional: ${point['total_notional']:,.2f}
        L/S Ratio: {point['ls_ratio']:.3f}
        Price: ${point['current_price']:,.2f}
        {'-' * 50}""")

def _print_global_metrics(metrics: List[Dict]) -> None:
    """Format and print global metrics data.
    
    Args:
        metrics (List[Dict]): List of global metrics data points
    """
    if not metrics:
        print(f"{Fore.YELLOW}No global metrics found{Style.RESET_ALL}")
        return
        
    print(f"\n{Fore.CYAN}Global Market Metrics:{Style.RESET_ALL}")
    for metric in metrics:
        _print_metric_entry(metric)

def _print_metric_entry(metric: Dict) -> None:
    """Print a single metric entry.
    
    Args:
        metric (Dict): Metric data dictionary
    """
    print(f"""
    {Fore.GREEN}Timestamp: {metric['timestamp']}{Style.RESET_ALL}
    Total Volume: ${metric['total_notional_volume']:,.2f}
    Global L/S Ratio: {metric['global_ls_ratio']:.3f}
    Long Positions: {metric['long_positions_count']}
    Short Positions: {metric['short_positions_count']}
    {'-' * 50}""")