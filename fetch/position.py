from typing import Dict
from config.settings import BASE_URLS
from .utils import fetch_website

def fetch_position() -> Dict:
    postitions_data = fetch_website(BASE_URLS['position'])
    return postitions_data
