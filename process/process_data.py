import json
from datetime import datetime

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
    with open(f'data/{file_path}', 'w') as f:
        json.dump(data, f, indent=4)

def process_analytics_positions(input_file, output_file):
    """
    Processes analytics positions data and saves a summary.

    Args:
        input_file (str): The input JSON file with positions data.
        output_file (str): The output JSON file for the summary.
    """
    try:
        data = load_json(input_file)
        position_data = data.get('data', [])
        total_notional = sum(pos.get('Total Notional', 0) for pos in position_data)
        total_long_notional = sum(
            pos.get('Majority Side Notional', 0) if pos.get('Majority Side') == 'LONG' else pos.get('Minority Side Notional', 0)
            for pos in position_data
        )
        total_short_notional = total_notional - total_long_notional
        total_long_positions = sum(pos.get('Number Long', 0) for pos in position_data)
        total_short_positions = sum(pos.get('Number Short', 0) for pos in position_data)
        assets_count = len(position_data)
        ls_ratio = (total_long_notional / total_notional) if total_notional != 0 else 0
        
        summary = {
            'total_notional': total_notional,
            'total_long_notional': total_long_notional,
            'total_short_notional': total_short_notional,
            'number_of_assets': assets_count,
            'total_long_positions': total_long_positions,
            'total_short_positions': total_short_positions,
            'ls_ratio': ls_ratio
        }
        
        save_json(summary, output_file)
        print(f"Summary successfully saved to {output_file}")
    
    except Exception as e:
        print(f"Error processing data: {e}")

def process_liquidation_data(input_file, output_file):
    """
    Processes liquidation data and saves a summary.

    Args:
        input_file (str): The input JSON file with liquidation data.
        output_file (str): The output JSON file for the summary.
    """
    try:
        data = load_json(input_file)
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
        
        save_json(summary, output_file)
        print(f"Liquidation summary successfully saved to {output_file}")
    
    except Exception as e:
        print(f"Error processing data: {e}")

def process_candle_data(input_file, output_file):
    """
    Processes candle data and converts timestamps to date format.

    Args:
        input_file (str): The input JSON file with candle data.
        output_file (str): The output JSON file for the processed data.
    """
    try:
        data = load_json(input_file)
        processed_data = [
            {**entry, 'date': datetime.utcfromtimestamp(entry['timestamp'] // 1000).strftime('%Y/%m/%d')}
            for entry in data
        ]
        save_json(processed_data, output_file)
        print(f"Candle data successfully saved to {output_file}")
    
    except Exception as e:
        print(f"Error processing data: {e}")
