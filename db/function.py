"""
Database interaction functions for InfluxDB operations.

This module provides high-level functions for reading from and writing to InfluxDB,
with comprehensive error handling, data validation, and formatted output.
"""

import asyncio
import logging
from functools import wraps
from typing import Dict, List, Optional, Tuple
from colorama import Fore, Style
from .influx_reader import InfluxReader
from .influx_writer import InfluxWriter


def handle_db_errors(func):
    """Decorator for handling database operation errors.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_msg = f"Database error in {func.__name__}: {str(e)}"
            logging.error(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
            return None
    return wrapper


@handle_db_errors
async def write_to_influx(validated_position_data: Optional[List],
                          validated_global_position_data: Optional[Dict],
                          batch_size: int = 10) -> Tuple[int, int]:
    """Write validated data to InfluxDB with improved error handling and batch processing.
    
    The handle_db_errors decorator wraps this function to provide consistent error handling.
    If any database errors occur, the decorator will:
    1. Log the error with the function name and error details
    2. Return None instead of propagating the exception
    3. Format the error message with red coloring for visibility

    Args:
        validated_position_data: List of position data to write
        validated_global_position_data: Global market data to write
        batch_size: Number of records to write in each batch

    Returns:
        Tuple[int, int]: (successful writes, failed writes)
    """
    influx_writer = None
    successful_writes = 0
    failed_writes = 0

    try:
        influx_writer = InfluxWriter()

        if validated_position_data:
            # Process in batches
            for i in range(0, len(validated_position_data), batch_size):
                batch = validated_position_data[i:i + batch_size]
                try:
                    await asyncio.gather(*[
                        _write_position(influx_writer, position)
                        for position in batch
                    ])
                    successful_writes += len(batch)
                except Exception as e:
                    failed_writes += len(batch)
                    logging.error(f"Batch write error: {e}")

        if validated_global_position_data:
            try:
                await _write_global_data(influx_writer, validated_global_position_data)
                successful_writes += 1
            except Exception as e:
                failed_writes += 1
                logging.error(f"Global data write error: {e}")

        return successful_writes, failed_writes

    finally:
        if influx_writer:
            influx_writer.close()


async def _write_position(writer: InfluxWriter, position: Dict) -> None:
    """Write a single position record.

    Args:
        writer: InfluxDB writer instance
        position: Position data to write
    """
    try:
        writer.write_position_data([position])
    except Exception as e:
        logging.error(
            f"Error writing position data for {
                position.get(
                    'asset',
                    'Unknown')}: {e}")
        raise


async def _write_global_data(writer: InfluxWriter, global_data: Dict) -> None:
    """Write global market data.

    Args:
        writer: InfluxDB writer instance
        global_data: Global market data to write
    """
    try:
        writer.write_global_position(global_data)
    except Exception as e:
        logging.error(f"Error writing global position data: {e}")
        raise


def read_from_influx(data_type: str = 'latest_positions',
                     asset: Optional[str] = None,
                     hours: int = 24,
                     format_output: bool = True,
                     time_bucket: str = '1h') -> List[Dict]:
    """Read data from InfluxDB with enhanced query options and formatting.

    Args:
        data_type: Type of data to read ('latest_positions', 'asset_history', 'global_metrics')
        asset: Asset symbol for asset-specific queries
        hours: Number of hours of historical data to retrieve
        format_output: Whether to print formatted output
        time_bucket: Time bucket for aggregating data ('1h', '1d', etc.)

    Returns:
        List[Dict]: Query results
    """
    reader = None
    try:
        reader = InfluxReader()

        # Validate input parameters
        if not _validate_query_params(data_type, asset, hours):
            return []

        # Execute query based on type
        data = _execute_query(reader, data_type, asset, hours)

        # Format and display if requested
        if format_output and data:
            _format_output(data_type, data, asset)

        return data

    except Exception as e:
        logging.error(
            f"{Fore.RED}Error reading from InfluxDB: {e}{Style.RESET_ALL}")
        return []
    finally:
        if reader:
            reader.close()


def _validate_query_params(
        data_type: str, asset: Optional[str], hours: int) -> bool:
    """Validate query parameters.

    Args:
        data_type: Type of data query
        asset: Asset symbol
        hours: Historical hours

    Returns:
        bool: Whether parameters are valid
    """
    valid_types = {'latest_positions', 'asset_history', 'global_metrics'}
    if data_type not in valid_types:
        logging.error(
            f"Invalid data type: {data_type}. Must be one of {valid_types}")
        return False

    if data_type == 'asset_history' and not asset:
        logging.error("Asset symbol required for asset_history query")
        return False

    if hours <= 0:
        logging.error("Hours must be positive")
        return False

    return True


def _execute_query(reader: InfluxReader, data_type: str,
                   asset: Optional[str], hours: int) -> List[Dict]:
    """Execute the appropriate query based on type.

    Args:
        reader: InfluxDB reader instance
        data_type: Type of query to execute
        asset: Asset symbol
        hours: Historical hours

    Returns:
        List[Dict]: Query results
    """
    if data_type == 'latest_positions':
        return reader.get_latest_positions()
    elif data_type == 'asset_history':
        return reader.get_asset_history(asset, hours)
    else:  # global_metrics
        return reader.get_global_metrics(hours)


def _format_output(
        data_type: str, data: List[Dict], asset: Optional[str] = None) -> None:
    """Format and display query results.

    Args:
        data_type: Type of data to format
        data: Data to format
        asset: Asset symbol for context
    """
    if not data:
        print(f"{Fore.YELLOW}No data found for query{Style.RESET_ALL}")
        return

    formatters = {
        'latest_positions': _print_position_data,
        'asset_history': lambda d: _print_asset_history(d, asset),
        'global_metrics': _print_global_metrics
    }

    formatter = formatters.get(data_type)
    if formatter:
        formatter(data)


def _print_position_data(positions: List[Dict]) -> None:
    """Format and print position data with enhanced formatting.

    Args:
        positions: List of position data to print
    """
    if not positions:
        print(f"{Fore.YELLOW}No position data found{Style.RESET_ALL}")
        return

    print(f"\n{Fore.CYAN}Latest Position Data:{Style.RESET_ALL}")

    # Sort positions by total notional value
    sorted_positions = sorted(
        positions, key=lambda x: x.get(
            'total_notional', 0), reverse=True)

    for pos in sorted_positions:
        _print_position_entry(pos)

    # Print summary
    total_notional = sum(p.get('total_notional', 0) for p in positions)
    avg_ls_ratio = sum(p.get('ls_ratio', 0)
                       for p in positions) / len(positions)
    print(f"""
        {Fore.CYAN}Summary:{Style.RESET_ALL}
        Total Market Value: ${total_notional:,.2f}
        Average L/S Ratio: {avg_ls_ratio:.3f}
        Number of Assets: {len(positions)}
        """)


def _print_position_entry(pos: Dict) -> None:
    """Print a single position entry with enhanced formatting.

    Args:
        pos: Position data dictionary
    """
    # Determine color based on L/S ratio
    ls_color = Fore.GREEN if pos.get('ls_ratio', 0) > 1 else Fore.RED

    print(f"""
        {Fore.CYAN}Asset: {pos['asset']}{Style.RESET_ALL}
            Total Notional: ${pos['total_notional']:,.2f}
            L/S Ratio: {ls_color}{pos['ls_ratio']:.3f}{Style.RESET_ALL}
            Current Price: ${pos['current_price']:,.2f}
            Traders: {Fore.GREEN}{pos['traders_long']}{Style.RESET_ALL} long, {Fore.RED}{pos['traders_short']}{Style.RESET_ALL} short
            Timestamp: {pos['timestamp']}
        {'-' * 60}""")


def _print_asset_history(history: List[Dict], asset: str) -> None:
    """Format and print asset history data with enhanced formatting.

    Args:
        history: List of historical data points
        asset: Asset symbol
    """
    if not history:
        print(f"{Fore.YELLOW}No historical data found for {asset}{Style.RESET_ALL}")
        return

    print(f"\n{Fore.CYAN}Historical Data for {asset}:{Style.RESET_ALL}")

    # Calculate price changes
    for i in range(len(history)):
        if i > 0:
            prev_price = history[i - 1]['current_price']
            curr_price = history[i]['current_price']
            price_change = ((curr_price - prev_price) / prev_price) * 100
            history[i]['price_change'] = price_change

    for point in history:
        _print_history_point(point)

    # Print summary
    start_price = history[-1]['current_price']
    end_price = history[0]['current_price']
    total_change = ((end_price - start_price) / start_price) * 100

    print(f"""
        {Fore.CYAN}Summary:{Style.RESET_ALL}
        Period: {history[-1]['timestamp']} to {history[0]['timestamp']}
        Total Price Change: {Fore.GREEN if total_change >= 0 else Fore.RED}{total_change:+.2f}%{Style.RESET_ALL}
        Starting Price: ${start_price:,.2f}
        Ending Price: ${end_price:,.2f}
        """)


def _print_history_point(point: Dict) -> None:
    """Print a single history data point with enhanced formatting.

    Args:
        point: Historical data point dictionary
    """
    price_change = point.get('price_change')
    change_color = Fore.GREEN if price_change and price_change >= 0 else Fore.RED
    change_str = f"{change_color}{
        price_change:+.2f}%{
        Style.RESET_ALL}" if price_change is not None else "N/A"

    print(f"""
        {Fore.CYAN}Timestamp: {point['timestamp']}{Style.RESET_ALL}
            Total Notional: ${point['total_notional']:,.2f}
            L/S Ratio: {point['ls_ratio']:.3f}
            Price: ${point['current_price']:,.2f} ({change_str})
        {'-' * 60}""")


def _print_global_metrics(metrics: List[Dict]) -> None:
    """Format and print global metrics data with enhanced formatting.

    Args:
        metrics: List of global metrics data points
    """
    if not metrics:
        print(f"{Fore.YELLOW}No global metrics found{Style.RESET_ALL}")
        return

    print(f"\n{Fore.CYAN}Global Market Metrics:{Style.RESET_ALL}")

    # Calculate volume changes
    for i in range(len(metrics)):
        if i > 0:
            prev_vol = metrics[i - 1]['total_notional_volume']
            curr_vol = metrics[i]['total_notional_volume']
            vol_change = ((curr_vol - prev_vol) / prev_vol) * 100
            metrics[i]['volume_change'] = vol_change

    for metric in metrics:
        _print_metric_entry(metric)

    # Print summary
    start_vol = metrics[-1]['total_notional_volume']
    end_vol = metrics[0]['total_notional_volume']
    total_change = ((end_vol - start_vol) / start_vol) * 100

    print(f"""
        {Fore.CYAN}Summary:{Style.RESET_ALL}
        Period: {metrics[-1]['timestamp']} to {metrics[0]['timestamp']}
        Total Volume Change: {Fore.GREEN if total_change >= 0 else Fore.RED}{total_change:+.2f}%{Style.RESET_ALL}
        Starting Volume: ${start_vol:,.2f}
        Ending Volume: ${end_vol:,.2f}
        """)


def _print_metric_entry(metric: Dict) -> None:
    """Print a single metric entry with enhanced formatting.

    Args:
        metric: Metric data dictionary
    """
    volume_change = metric.get('volume_change')
    change_color = Fore.GREEN if volume_change and volume_change >= 0 else Fore.RED
    change_str = f"{change_color}{
        volume_change:+.2f}%{
        Style.RESET_ALL}" if volume_change is not None else "N/A"

    ls_color = Fore.GREEN if metric['global_ls_ratio'] > 1 else Fore.RED

    print(f"""
        {Fore.CYAN}Timestamp: {metric['timestamp']}{Style.RESET_ALL}
            Total Volume: ${metric['total_notional_volume']:,.2f} ({change_str})
            Global L/S Ratio: {ls_color}{metric['global_ls_ratio']:.3f}{Style.RESET_ALL}
            Long Positions: {Fore.GREEN}{metric['long_positions_count']}{Style.RESET_ALL}
            Short Positions: {Fore.RED}{metric['short_positions_count']}{Style.RESET_ALL}
        {'-' * 60}""")
