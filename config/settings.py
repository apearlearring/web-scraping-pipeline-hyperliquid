from datetime import datetime

# API URLs
BASE_URLS = {
    'position': 'https://api.hyperdash.info/summary',
    'ls_trend': 'https://api.hyperdash.info/ls_trend',
    'funding_history': 'https://api.hyperliquid.xyz/info',
    'liquidation': 'https://hyperdash.info/api/liquidation-data-v2'
}

# API Keys and Headers
LIQUIDATION_HEADERS = {
    'X-Api-Key': 'hyperdash_public_7vN3mK8pQ4wX2cL9hF5tR1bY6gS0jD'
}

ZENROW_API_KEY = "9f8dac77494ff7542294669eb4e8cc7b652584ef"

ASSET_HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}

# Supported Cryptocurrencies
CRYPTO_NAMES = ["FTM", "CHILLGUY", "ME"]

# Time Settings
UPDATE_INTERVAL = 60  # seconds
LIQUIDATION_DAYS = 7
HISTORICAL_DAYS = 8

# Calculate timestamps
CURRENT_TIME = int(datetime.now().timestamp() * 1000)
START_TIME = CURRENT_TIME - (LIQUIDATION_DAYS * 24 * 60 * 60 * 1000)
END_TIME = CURRENT_TIME

# Data Processing Settings
PRICE_INTERVAL = 1000  # Price interval for liquidation grouping
PRECISION = 2  # Decimal places for amounts

# File Paths
DATA_DIR = 'data'

# Request Settings
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Validation Settings
VALID_POSITION_TYPES = ["LONG", "SHORT"]

INFLUXDB_TOKEN = "xxb_17nmmKGT9xbbEToJbCsyTeLFELMnoBH54Xwk3Tjc6M9m0XVlRLlvuBNWLwBXZnwb8j3h7KR02as8GZePoQ=="
INFLUXDB_ORG = "Omo-Protocol"
INFLUXDB_BUCKET = "HL-Scraping-Pipeline"
INFLUXDB_COMPRESSED_BUCKET = "HL-Scraping-Pipeline-Compressed"
INFlUXDB_URL = "http://localhost:8086"

# Data Retention Settings
INFLUXDB_RETENTION_PERIOD = "7d"  # Raw data retention
INFLUXDB_COMPRESSION_MIN_AGE = "24h"  # When to start compressing data
INFLUXDB_COMPRESSED_RETENTION = "90d"  # How long to keep compressed data
INFLUXDB_COMPRESSION_INTERVAL = "1h"  # Interval for compression task
INFLUXDB_DOWNSAMPLING_WINDOW = "1h"  # Window for data aggregation
