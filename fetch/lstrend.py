from typing import Dict

from config.settings import BASE_URLS

from .utils import fetch_website


def fetch_ls_trend() -> Dict:
    try:
        ls_trend_data = fetch_website(BASE_URLS['ls_trend'])
        return ls_trend_data
    except Exception as e:
        print(f"Error fetching L/S trend data: {e}")
        return None
