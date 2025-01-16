from typing import Dict


def process_global_position(data: Dict) -> Dict:
    """
    Processes analytics positions data and returns a summary.

    Args:
        data (dict): The input data with positions.

    Returns:
        dict: A summary of the analytics positions.
    """
    try:
        position_data = data.get('data', [])
        total_notional_volume = sum(
            pos.get(
                'Total Notional',
                0) for pos in position_data)
        long_positions_notional = sum(
            pos.get(
                'Majority Side Notional',
                0) if pos.get('Majority Side') == 'LONG' else pos.get(
                'Minority Side Notional',
                0)
            for pos in position_data
        )
        short_positions_notional = total_notional_volume - long_positions_notional
        long_positions_count = sum(pos.get('Number Long', 0)
                                   for pos in position_data)
        short_positions_count = sum(pos.get('Number Short', 0)
                                    for pos in position_data)
        total_tickers = len(position_data)
        global_ls_ratio = (
            long_positions_notional /
            total_notional_volume) if total_notional_volume != 0 else 0

        global_position = {
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

        return global_position

    except Exception as e:
        print(f"Error processing data: {e}")
