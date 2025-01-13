import json
from datetime import datetime
from utils.directory import ensure_data_directory

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
    Processes liquidation data and returns a summary suitable for a distribution chart.
    For each price level:
    - Negative amounts only contribute to cumulative shorts (cumulative longs = 0)
    - Positive amounts only contribute to cumulative longs (cumulative shorts = 0)

    Args:
        data (dict): The input data with liquidation details.
        asset_name (str): The name of the asset.

    Returns:
        dict: A summary of the liquidation distribution data.
    """
    try:
        distribution = []
        total_longs = 0  # Track total long liquidations
        total_shorts = 0  # Track total short liquidations
        interval = 1000  # Adjust interval as needed

        # Group data into intervals
        grouped_data = {}
        
        # First pass: collect all liquidations
        for price, wallets in data.items():
            price_value = float(price)
            interval_key = int(price_value // interval * interval)
            
            if interval_key not in grouped_data:
                grouped_data[interval_key] = {'long': 0, 'short': 0}
            
            # Calculate liquidations at this price level
            for amount in wallets.values():
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
                # If there are long liquidations, only show cumulative longs
                distribution.append({
                    'price': interval_key,
                    'long_liquidations': round(long_liquidations, 2),
                    'short_liquidations': 0,
                    'cumulative_longs': round(total_longs, 2),
                    'cumulative_shorts': 0
                })
            elif short_liquidations > 0:
                # If there are short liquidations, only show cumulative shorts
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

        summary = {
            'asset': asset_name,
            'distribution': distribution,
            'current_price': current_price,
            'timestamp': str(datetime.now()),
            'update_interval': 60,
            'base_currency': 'USD',
            'precision': 2,
            'total_long_liquidations': round(total_longs, 2),
            'total_short_liquidations': round(total_shorts, 2)
        }
        
        # Save the summary to a JSON file
        file_name = f"data/liquidation_metrics_{asset_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_json(summary, file_name)
        print(f"Liquidation metrics saved to {file_name}")
        
        return summary
    
    except Exception as e:
        print(f"Error processing data: {e}")
