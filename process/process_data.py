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
    with open(f'data/{file_path}', 'w') as f:
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

def process_liquidation_data(data):
    """
    Processes liquidation data and returns a summary.

    Args:
        data (dict): The input data with liquidation details.

    Returns:
        dict: A summary of the liquidation data.
    """
    try:
        total_long_liquidation = 0
        total_short_liquidation = 0
        largest_liquidation = 0
        total_liquidation = 0

        for price, wallets in data.items():
            price_value = float(price)
            for amount in wallets.values():
                liquidation_value = price_value * abs(amount)
                total_liquidation += liquidation_value
                largest_liquidation = max(largest_liquidation, liquidation_value)

                if amount > 0:
                    total_long_liquidation += liquidation_value
                else:
                    total_short_liquidation += liquidation_value

        summary = {
            'total_long_liquidation': total_long_liquidation,
            'total_short_liquidation': total_short_liquidation,
            'largest_liquidation': largest_liquidation,
            'total_liquidation': total_liquidation
        }
        
        return summary
    
    except Exception as e:
        print(f"Error processing data: {e}")
