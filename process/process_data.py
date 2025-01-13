import json
from datetime import datetime
from utils.directory import ensure_data_directory
from typing import Dict, List


def load_json(file_path):
    """
    Loads JSON data from a file.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The loaded JSON data.
    """
    with open(f'data/{file_path}', 'r') as f:
        return json.load(f)

def save_json(data, file_path):
    """
    Saves data to a JSON file.

    Args:
        data (dict): The data to save.
        file_path (str): The path to the JSON file.
    """
    ensure_data_directory()
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def process_analytics_positions(data):
    """
    Processes analytics positions data and returns a summary.

    Args:
        data (dict): The input data with positions.

    Returns:
        dict: A summary of the analytics positions.
    """
    try:
        position_data = data.get('data', [])
        total_notional_volume = sum(pos.get('Total Notional', 0) for pos in position_data)
        long_positions_notional = sum(
            pos.get('Majority Side Notional', 0) if pos.get('Majority Side') == 'LONG' else pos.get('Minority Side Notional', 0)
            for pos in position_data
        )
        short_positions_notional = total_notional_volume - long_positions_notional
        long_positions_count = sum(pos.get('Number Long', 0) for pos in position_data)
        short_positions_count = sum(pos.get('Number Short', 0) for pos in position_data)
        total_tickers = len(position_data)
        global_ls_ratio = (long_positions_notional / total_notional_volume) if total_notional_volume != 0 else 0
        
        summary = {
            'total_notional_volume': total_notional_volume,
            'long_positions_notional': long_positions_notional,
            'short_positions_notional': short_positions_notional,
            'total_tickers': total_tickers,
            'long_positions_count': long_positions_count,
            'short_positions_count': short_positions_count,
            'global_ls_ratio': global_ls_ratio,
            "base_currency": "USD",
            "timestamp": data.get('lastUpdated', str)
        }
        
        return summary
    
    except Exception as e:
        print(f"Error processing data: {e}")

def process_liquidation_data(data, asset_name):
    """
    Processes liquidation data and returns a summary suitable for a distribution chart
    along with liquidation metrics.

    Args:
        data (dict): The input data with liquidation details.
        asset_name (str): The name of the asset.

    Returns:
        dict: A summary of the liquidation distribution data and metrics.
    """
    try:
        # Distribution-related variables
        distribution = []
        total_longs = 0
        total_shorts = 0
        interval = 500

        # Metrics-related variables
        largest_single = 0
        
        # Group data into intervals
        grouped_data = {}
        
        # First pass: collect all liquidations and calculate metrics
        for price, wallets in data.items():
            price_value = float(price)
            interval_key = int(price_value // interval * interval)
            
            if interval_key not in grouped_data:
                grouped_data[interval_key] = {'long': 0, 'short': 0}
            
            # Calculate liquidations and metrics at this price level
            for amount in wallets.values():
                abs_amount = abs(amount)
                largest_single = max(largest_single, abs_amount)
                
                if amount > 0:  # Long liquidation
                    grouped_data[interval_key]['long'] += amount
                    total_longs += amount
                else:  # Short liquidation (negative value)
                    grouped_data[interval_key]['short'] += abs(amount)
                    total_shorts += abs(amount)

        # Process the grouped data in price order
        for interval_key in sorted(grouped_data.keys()):
            long_liquidations = grouped_data[interval_key]['long']
            short_liquidations = grouped_data[interval_key]['short']

            if long_liquidations > 0:
                distribution.append({
                    'price': interval_key,
                    'long_liquidations': round(long_liquidations, 2),
                    'short_liquidations': 0,
                    'cumulative_longs': round(total_longs, 2),
                    'cumulative_shorts': 0
                })
            elif short_liquidations > 0:
                distribution.append({
                    'price': interval_key,
                    'long_liquidations': 0,
                    'short_liquidations': round(short_liquidations, 2),
                    'cumulative_longs': 0,
                    'cumulative_shorts': round(total_shorts, 2)
                })

        # Get current price
        prices = sorted([float(price) for price in data.keys()])
        current_price = prices[-1] if prices else 0

        # Calculate total volume for metrics
        total_volume = total_longs + total_shorts

        # Combine distribution and metrics in the summary
        liquidation_distribution = {
            'asset': asset_name,
            'distribution': distribution,
            'current_price': current_price,
            'timestamp': str(datetime.now()),
            'update_interval': 60,
            'base_currency': 'USD',
            'precision': 2,
            # Add metrics section
        }

        liquidation_metrics =  {
                'total_long_liquidation': round(total_longs, 8),
                'total_short_liquidation': round(total_shorts, 8),
                'largest_liquidation': round(largest_single, 8),
                'total_liquidation': round(total_volume, 8)
            }
        return liquidation_metrics, liquidation_distribution
    
    except Exception as e:
        print(f"Error processing {asset_name}: {e}")
        return None, None

def process_ls_trend_data(json_data: List[dict]) -> List[dict]:
    """
    Process raw L/S trend JSON data into LSTrendData objects.
    
    Args:
        json_data: List of dictionaries containing asset trend data
        
    Returns:
        List of LSTrendData objects
    """
    result = []
    
    for asset_data in json_data:
        asset_name = asset_data["Asset"]
        points = []
        
        # Get all dates except "Asset" key
        dates = [k for k in asset_data.keys() if k != "Asset"]
        dates.sort()  # Sort dates chronologically
        
        prev_ratio = None
        for date_str in dates:
            # Skip empty values
            if asset_data[date_str] == "":
                continue
                
            ratio = float(asset_data[date_str])
            
            # Determine majority side based on ratio change from previous day
            if prev_ratio is None:
                majority_side = "LONG" if ratio >= 50 else "SHORT"
            else:
                majority_side = "LONG" if ratio > prev_ratio else "SHORT"
            
            # Create point data
            point = {
                "timestamp": datetime.strptime(date_str, "%Y-%m-%d"),
                "ls_ratio": ratio,
                "majority_side": majority_side,
                "notional_delta": abs(50 - ratio) # Distance from neutral (50/50)
            }
            points.append(point)
            prev_ratio = ratio
            
        # Only create trend data if we have points
        if points:
            trend = {
                "asset": asset_name,
                "points": points,
                "last_updated": max(p["timestamp"] for p in points),
                "update_frequency": "daily",
                "historical_days": len(points)
            }
            result.append(trend)
            
    return result