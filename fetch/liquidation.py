import json
from typing import Dict
from config.settings import BASE_URLS, LIQUIDATION_HEADERS
from .utils import fetch_website 

def fetch_liquidation(asset_name : str, days: int = 7) -> Dict:
    liquidation_url = f"{BASE_URLS['liquidation']}?ticker={asset_name}&days={days}"
    liquidation_data = fetch_website(liquidation_url, headers=LIQUIDATION_HEADERS)
    return liquidation_data