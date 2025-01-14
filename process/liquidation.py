from typing import Dict
from datetime import datetime

def process_liquidation(liquidation_data : Dict, asset_name : str) -> Dict:
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
        for price, wallets in liquidation_data.items():
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
        prices = sorted([float(price) for price in liquidation_data.keys()])
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

