from zenrows import ZenRowsClient
from typing import Dict, Optional
import asyncio
from config.settings import ZENROW_API_KEY
from utils.directory import ensure_data_directory


client = ZenRowsClient(ZENROW_API_KEY)

async def fetch_website(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    page_settings: Optional[Dict[str, str]] = None,
    max_retries: int = 3
):
    """
    Fetches data from a website using ZenRows API and returns it as a JSON object.

    Args:
        url (str): The URL to fetch data from.
        headers (Optional[Dict[str, str]]): Additional headers for the request.
        page_settings (Optional[Dict[str, str]]): Settings for the page, such as method and body for POST requests.
        max_retries (int): Maximum number of retries for fetching data.

    Returns:
        dict: The fetched data as a JSON object.
    """
    print(url)
    ensure_data_directory()

    retries = 0
    while retries < max_retries:
        try:
            if page_settings and page_settings.get('method') == 'POST':
                response = client.post(url, headers=headers, data=page_settings.get('body'))
            else:
                response = client.get(url, headers=headers)

            if response.status_code == 200:
                # print(response.json())
                return response.json()
            elif response.status_code in [401, 403]:
                print(f"Authorization error (status {response.status_code}) - check your API key")
                return None
            elif response.status_code in [429, 503]:
                raise Exception(f"Rate limit or service unavailable: {response.status_code}")
            else:
                raise Exception(f"HTTP error: {response.status_code}")

        except Exception as e:
            print(f"Error occurred: {e}")
            retries += 1
            if retries < max_retries:
                wait_time = 2 ** retries  # Exponential backoff (in seconds)
                print(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                print("Max retries reached. Exiting.")
                return None

    return None
