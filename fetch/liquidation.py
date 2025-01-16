import json
import logging
from typing import Dict

from config.settings import BASE_URLS, LIQUIDATION_HEADERS

from .utils import fetch_website


def fetch_liquidation(asset_name: str, days: int = 7) -> Dict:
    try:
        liquidation_url = f"{
            BASE_URLS['liquidation']}?ticker={asset_name}&days={days}"
        liquidation_data = fetch_website(
            liquidation_url, headers=LIQUIDATION_HEADERS)

        logging.critical(liquidation_data)

        return liquidation_data
    except Exception as e:
        print(f"Error fetching liquidation data for {asset_name}: {e}")
        return None
