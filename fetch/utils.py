import asyncio
import json
from typing import Dict, Optional

from pyppeteer import launch

from utils.directory import ensure_data_directory


async def fetch_website(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    page_settings: Optional[Dict[str, str]] = None,
    max_retries: int = 3
):
    """
    Fetches data from a website and returns it as a JSON object.

    Args:
        url (str): The URL to fetch data from.
        headers (Optional[Dict[str, str]]): Additional headers for the request.
        page_settings (Optional[Dict[str, str]]): Settings for the page, such as method and body for POST requests.
        max_retries (int): Maximum number of retries for fetching data.

    Returns:
        dict: The fetched data as a JSON object.
    """
    ensure_data_directory()

    browser = await launch(
        headless=True,
        executablePath='C:/Program Files/Google/Chrome/Application/chrome.exe',
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            '--window-size=1920,1080'
        ]
    )

    try:
        page = await browser.newPage()
        default_headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'en-US,en;q=0.9',
            'connection': 'keep-alive',
            'referer': 'https://hyperdash.info/liqmap',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }

        if headers:
            default_headers.update(headers)

        await page.setViewport({'width': 1920, 'height': 1080})
        await page.setExtraHTTPHeaders(default_headers)

        retries = 0
        while retries < max_retries:
            try:
                if page_settings and page_settings.get('method') == 'POST':
                    # Handle POST requests
                    response = await page.evaluate(
                        '''async (url, body) => {
                            const response = await fetch(url, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: body
                            });
                            return await response.json();
                        }''',
                        url,
                        page_settings['body']
                    )
                else:
                    # Handle GET requests
                    response = await page.goto(url, {
                        'waitUntil': 'networkidle0',
                        'timeout': 30000
                    })

                    if response.status in [429, 503]:
                        raise Exception(f"Received status {response.status}")

                    if response.status == 401:
                        print("Authentication error - check your API key")
                        return
                    elif not response.ok:
                        print(f"HTTP error: {response.status}")
                        return

                    content = await page.evaluate('() => document.querySelector("body").innerText')
                    response = json.loads(content)

                return response

            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                break
            except Exception as e:
                print(f"Error occurred: {e}")
                retries += 1
                if retries < max_retries:
                    wait_time = 2 ** retries
                    print(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    print("Max retries reached. Exiting.")
                    break

    finally:
        await browser.close()
