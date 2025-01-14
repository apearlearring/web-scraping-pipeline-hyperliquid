from typing import Dict, List, Tuple
from process.utils import *

class DataProcessor:
    @staticmethod
    def process_crypto_data(
        crypto_name: str,
        liquidation_data: Dict,
        funding_history: Dict,
        assets_position_data: Dict,
        ls_trend_data: List[Dict]
    ) -> Tuple[Dict, Dict, Dict]:
        """
        Processes data for a specific cryptocurrency.
        """
        liquidation_metrics, liquidation_distribution = process_liquidation_data(
            liquidation_data, crypto_name
        )

        # Find and update asset position data
        asset_position = next(
            (asset for asset in assets_position_data['data'] 
             if asset['Asset'] == crypto_name),
            None
        )
        
        if asset_position:
            asset_position.update({
                'Liquidation_Metrics': liquidation_metrics,
                'Funding_History': funding_history[-1],
                'Timestamp': assets_position_data["lastUpdated"]
            })

        # Find corresponding L/S trend data
        ls_trend = next(
            (trend for trend in ls_trend_data 
             if trend['Asset'] == crypto_name),
            None
        )

        return asset_position, liquidation_distribution, ls_trend
