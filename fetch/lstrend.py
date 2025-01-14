from typing import Dict
from config.settings import BASE_URLS
from .utils import fetch_website

def fetch_ls_trend() -> Dict:
    ls_trend_data = fetch_website(BASE_URLS['ls_trend'])
    return ls_trend_data

