# Scrapping Pipeline from HyperLiquid 

This project is webscraping pipeline that gathers comprehensive trading data from hyperdash.info (including subpages such as /analytics, /liqmap, /ticker/*) for use in a short-horizon price-direction/volatility predictor.

## Project Structure

- **fetch/**: Contains the `fetch_website.py` script for fetching data from websites.
- **process/**: Contains the `process_data.py` script for processing fetched data.
- **data/**: Directory where all fetched and processed JSON data files are stored.
- **main.py**: The main script to run the data fetching and processing tasks.

## Setup

### Prerequisites

- Python 3.7 or higher
- Google Chrome installed
- `pyppeteer` library

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/omo-protocol/hl-webscraping-puppeteer.git
   cd hl-webscraping-puppeteer
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure Google Chrome is installed and the path to the executable is correctly set in `fetch_website.py`.

## Usage

1. **Fetch and Process Data**: Run the main script to fetch and process data.
   ```bash
   python main.py
   ```

2. **Data Output**: Processed data will be saved in the `data/` directory as JSON files.

## Components

### fetch/fetch_website.py

- **Function**: `fetch_website`
  - Fetches data from a specified URL and saves it to a JSON file.
  - Supports both GET and POST requests with customizable headers and settings.

### process/process_data.py

- **Functions**:
  - `process_analytics_positions`: Processes analytics positions data and generates a summary.
  - `process_liquidation_data`: Processes liquidation data and calculates total and largest liquidations.
  - `process_candle_data`: Processes candle data and converts timestamps to a readable date format.

### main.py

- **Functions**:
  - `fetch_analytics`: Fetches and processes analytics data.
  - `fetch_liquidation`: Fetches and processes liquidation data for specified cryptocurrencies.
  - `fetch_asset`: Fetches asset funding history data.
  - `main`: Orchestrates the fetching and processing tasks.
