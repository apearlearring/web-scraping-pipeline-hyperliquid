import json
from config.settings import BASE_URLS
from typing import Dict
from datetime import datetime
from .utils import fetch_website



def fetch_funding_history(asset_name: str) -> Dict:
    try:
        asset_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

        funding_history_settings = {
            'method': 'POST',
            'body': json.dumps({
                "type": "fundingHistory",
                "coin": asset_name,
                "startTime": int((datetime.now().timestamp() - 10800) * 1000),
                "endTime": int(datetime.now().timestamp() * 1000)
            })
        }

        funding_history = fetch_website(BASE_URLS['funding_history'], headers = asset_headers, page_settings=funding_history_settings)

        return funding_history
    except Exception as e:
        print(f"Error fetching funding history for {asset_name}: {e}")
        return None
