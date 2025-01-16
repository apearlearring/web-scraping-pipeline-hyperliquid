from typing import Dict


def process_position(position_data: Dict, funding_history: str,
                     liquidation_metrics: Dict, lastupdated: str) -> Dict:
    try:
        position_data.update({
            'Funding_History': funding_history,
            'Liquidation_Metrics': liquidation_metrics,
            'Timestamp': lastupdated
        })

        return position_data

    except Exception as e:
        print(
            f"Error processing position data for {
                position_data['Asset']}: {e}")
        return None, None
