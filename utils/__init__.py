from typing import Dict, List

from .circuitbreaker import *
from .directory import *
from .loggingformat import *


def extract_crypto_names(position_data: Dict) -> List[str]:
    """Extract all unique crypto asset names from position data.

    Args:
        position_data (Dict): Position data dictionary containing 'data' list of positions

    Returns:
        List[str]: List of unique crypto asset names
    """
    try:
        if not position_data or 'data' not in position_data:
            return []

        return sorted(list({
            position['Asset']
            for position in position_data['data']
            if position.get('Asset')
        }))
    except Exception as e:
        print(f"Error extracting crypto names: {e}")
        return []