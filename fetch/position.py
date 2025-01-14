from typing import Dict
from config.settings import BASE_URLS
from .utils import fetch_website

def fetch_position() -> Dict:
    try:
        postitions_data = fetch_website(BASE_URLS['position'])
        return postitions_data
    except Exception as e:
        print(f"Error fetching position data: {e}")
        return None
