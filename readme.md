# HyperLiquid Scraping Pipeline

A robust data pipeline for gathering and analyzing cryptocurrency trading data from HyperLiquid's platform. This project implements comprehensive data collection, processing, and storage with failure handling and monitoring capabilities.

## Features

- **Real-time Data Collection**: Fetches trading data from hyperdash.info including:
  - Position analytics
  - Liquidation maps
  - Funding rates
  - Market metrics
- **Resilient Processing**: 
  - Circuit breaker pattern for failure prevention
  - Partial result handling
  - Batch processing with retries
- **Data Validation**: 
  - Schema validation using Pydantic
  - Data integrity checks
  - Error tracking
- **Persistent Storage**: 
  - InfluxDB integration for time-series data
  - Efficient querying capabilities
  - Data retention management
- **Comprehensive Monitoring**:
  - Colored logging output
  - Detailed failure tracking
  - Success rate monitoring
  - Performance metrics

## Project Structure

```
├── config/             # Configuration settings
│   ├── settings.py     # Global configuration
│   └── ...
├── db/                 # Database operations
│   ├── influx_base.py  # Base InfluxDB functionality
│   ├── influx_reader.py# Data reading operations
│   ├── influx_writer.py# Data writing operations
│   └── function.py     # High-level database functions
├── fetch/             # Data fetching modules
│   ├── liquidation.py  # Liquidation data fetching
│   ├── position.py     # Position data fetching
│   └── ...
├── process/           # Data processing modules
│   ├── position.py     # Position data processing
│   ├── liquidation.py  # Liquidation data processing
│   └── ...
├── utils/             # Utility modules
│   ├── circuitbreaker.py # Circuit breaker implementation
│   ├── loggingformat.py  # Logging configuration
│   ├── stats.py         # Statistics tracking
│   └── ...
├── validate/          # Data validation
│   ├── schema.py      # Data schemas
│   └── validate.py    # Validation functions
├── data/             # Data storage directory
├── main.py           # Main application entry
└── requirements.txt  # Project dependencies
```

## Prerequisites

- Python 3.7 or higher
- InfluxDB (2.0 or higher)
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/omo-protocol/hl-webscraping-pyppeteer.git
cd hl-webscraping-pyppeteer
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure InfluxDB:
- Install InfluxDB 2.0 or higher
- Create a bucket for the project
- Update settings in `config/settings.py` with your InfluxDB credentials

## Usage

### Running the Pipeline

1. Start data collection:
```bash
python main.py
```

2. View stored data:
```python
from db.function import read_from_influx

# View latest positions
read_from_influx('latest_positions')

# View asset history
read_from_influx('asset_history', asset='BTC', hours=24)

# View global metrics
read_from_influx('global_metrics')
```

### Monitoring

The pipeline provides real-time monitoring with colored output:
- 🟢 Green: Successful operations
- 🔴 Red: Failures and errors
- 🟡 Yellow: Warnings
- 🔵 Blue: Informational messages

### Batch Processing

The pipeline processes data in configurable batches:
```python
# Configure batch size in main.py
batch_processor = BatchProcessor(batch_size=5)
```

## Error Handling

The system implements multiple layers of error handling:

1. **Circuit Breaker**:
   - Prevents repeated failures
   - Configurable thresholds
   - Automatic recovery

2. **Partial Results**:
   - Continues processing despite partial failures
   - Records successful operations
   - Tracks failed operations

3. **Validation**:
   - Schema validation
   - Data integrity checks
   - Error reporting

## Data Storage

Data is stored in InfluxDB with the following structure:

1. **Position Metrics**:
   - Asset-specific positions
   - L/S ratios
   - Notional values
   - Trader counts
   - Position deltas
   - Funding rates
   - Open interest
   - Liquidation levels
   - Position concentration
   - Average entry prices

2. **Global Metrics**:
   - Total market volume
   - Global L/S ratios
   - Position counts
