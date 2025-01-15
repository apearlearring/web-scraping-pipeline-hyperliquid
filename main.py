import asyncio
from fetch import *
from process import *
from config.settings import CRYPTO_NAMES
from validate import *
from db import *
from datetime import datetime
import logging
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
import gc
from dataclasses import dataclass
from collections import defaultdict
from colorama import init, Fore, Style
from utils import extract_crypto_names

# Initialize colorama for Windows
init()

# Configure logging with colors
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors"""
    
    def format(self, record):
        if record.levelno == logging.ERROR:
            record.msg = f"{Fore.RED}{record.msg}{Style.RESET_ALL}"
        elif record.levelno == logging.WARNING:
            record.msg = f"{Fore.YELLOW}{record.msg}{Style.RESET_ALL}"
        elif record.levelno == logging.INFO:
            if "succeeded" in str(record.msg).lower():
                record.msg = f"{Fore.GREEN}{record.msg}{Style.RESET_ALL}"
            elif "failed" in str(record.msg).lower():
                record.msg = f"{Fore.RED}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

class CircuitBreaker:
    def __init__(self, failure_threshold=3, reset_timeout=300):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = defaultdict(int)
        self.last_failure_time = defaultdict(float)
        self.is_open = defaultdict(bool)

    def record_failure(self, operation_key: str):
        current_time = datetime.now().timestamp()
        if current_time - self.last_failure_time[operation_key] > self.reset_timeout:
            self.failures[operation_key] = 1
        else:
            self.failures[operation_key] += 1
        
        self.last_failure_time[operation_key] = current_time
        if self.failures[operation_key] >= self.failure_threshold:
            self.is_open[operation_key] = True

    def record_success(self, operation_key: str):
        self.failures[operation_key] = 0
        self.is_open[operation_key] = False

    def can_proceed(self, operation_key: str) -> bool:
        if not self.is_open[operation_key]:
            return True
        
        if datetime.now().timestamp() - self.last_failure_time[operation_key] > self.reset_timeout:
            self.is_open[operation_key] = False
            self.failures[operation_key] = 0
            return True
        
        return False

@dataclass
class FailureRecord:
    asset: str
    step: str
    error: str
    timestamp: datetime

@dataclass
class BatchStats:
    total_assets: int = 0
    successful_fetches: int = 0
    failed_fetches: int = 0
    successful_processes: int = 0
    failed_processes: int = 0
    successful_validations: int = 0
    failed_validations: int = 0
    successful_writes: int = 0
    failed_writes: int = 0
    failures: List[FailureRecord] = None

    def __post_init__(self):
        self.failures = []

    def record_failure(self, asset: str, step: str, error: str):
        self.failures.append(FailureRecord(
            asset=asset,
            step=step,
            error=str(error),
            timestamp=datetime.now()
        ))

    def print_failures(self):
        if not self.failures:
            logging.info(f"{Fore.GREEN}No failures recorded{Style.RESET_ALL}")
            return
            
        logging.error("Failure Details:")
        for failure in self.failures:
            logging.error(f"{Fore.RED}Asset: {failure.asset}")
            logging.error(f"Step: {failure.step}")
            logging.error(f"Error: {failure.error}")
            logging.error(f"Time: {failure.timestamp.strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
            logging.error("-" * 50)

async def fetch_asset_data(asset: str, circuit_breaker: CircuitBreaker, batch_stats: BatchStats) -> Dict:
    """Fetch all data for a single asset concurrently with circuit breaker"""
    operation_key = f"fetch_{asset}"
    if not circuit_breaker.can_proceed(operation_key):
        logging.warning(f"Circuit breaker open for {asset}, skipping fetch")
        batch_stats.record_failure(asset, "fetch", "Circuit breaker open")
        return None
    
    try:
        liquidation_data, funding_history = await asyncio.gather(
            fetch_liquidation(asset),
            fetch_funding_history(asset)
        )
        
        if liquidation_data is None and funding_history is None:
            circuit_breaker.record_failure(operation_key)
            batch_stats.record_failure(asset, "fetch", "Both liquidation and funding data are None")
            return None
            
        result = {
            'asset': asset,
            'liquidation_data': liquidation_data,
            'funding_history': funding_history
        }
        
        circuit_breaker.record_success(operation_key)
        return result
    except Exception as e:
        circuit_breaker.record_failure(operation_key)
        batch_stats.record_failure(asset, "fetch", str(e))
        logging.error(f"Error fetching data for {asset}: {e}")
        return None

async def process_asset_data(asset_data: Dict, position_data: Dict, timestamp: str, circuit_breaker: CircuitBreaker, batch_stats: BatchStats) -> Dict:
    """Process data for a single asset with partial result handling"""
    if not asset_data:
        return None
        
    asset = asset_data['asset']
    operation_key = f"process_{asset}"
    if not circuit_breaker.can_proceed(operation_key):
        logging.warning(f"Circuit breaker open for processing {asset}, skipping")
        batch_stats.record_failure(asset, "process", "Circuit breaker open")
        return None
    
    try:
        result = {}
        
        # Try processing each component separately
        try:
            processed_funding_history = process_funding_history(asset_data['funding_history'][-1]) if asset_data['funding_history'] else None
            result['funding_history'] = processed_funding_history
        except Exception as e:
            error_msg = f"Error processing funding history: {e}"
            logging.error(f"{asset}: {error_msg}")
            batch_stats.record_failure(asset, "process_funding", str(e))
        
        try:
            asset_position_data = next(
                (data for data in position_data['data'] if data['Asset'] == asset), 
                None
            )
            result['position_data'] = asset_position_data
        except Exception as e:
            error_msg = f"Error processing position data: {e}"
            logging.error(f"{asset}: {error_msg}")
            batch_stats.record_failure(asset, "process_position", str(e))
        
        try:
            if asset_data['liquidation_data']:
                liquidation_metrics, liquidation_distribution = process_liquidation(
                    liquidation_data=asset_data['liquidation_data'],
                    asset_name=asset
                )
                result['liquidation_metrics'] = liquidation_metrics
                result['liquidation_distribution'] = liquidation_distribution
        except Exception as e:
            error_msg = f"Error processing liquidation data: {e}"
            logging.error(f"{asset}: {error_msg}")
            batch_stats.record_failure(asset, "process_liquidation", str(e))
        
        # Only process position if we have at least some data
        if any(result.values()):
            try:
                processed_position = process_position(
                    position_data=result.get('position_data'),
                    funding_history=result.get('funding_history'),
                    liquidation_metrics=result.get('liquidation_metrics'),
                    lastupdated=timestamp
                )
                
                circuit_breaker.record_success(operation_key)
                return {
                    'position': processed_position,
                    'liquidation_distribution': result.get('liquidation_distribution')
                }
            except Exception as e:
                circuit_breaker.record_failure(operation_key)
                error_msg = f"Error in final position processing: {e}"
                logging.error(f"{asset}: {error_msg}")
                batch_stats.record_failure(asset, "process_final", str(e))
                return None
        
        circuit_breaker.record_failure(operation_key)
        batch_stats.record_failure(asset, "process", "No valid data to process")
        return None
        
    except Exception as e:
        circuit_breaker.record_failure(operation_key)
        batch_stats.record_failure(asset, "process", str(e))
        logging.error(f"Error processing data for {asset}: {e}")
        return None

async def batch_process_assets(assets: List[str], batch_size: int = 3):
    """Process assets in batches with improved error handling and stats tracking"""
    try:
        # Initialize circuit breaker and stats
        circuit_breaker = CircuitBreaker()
        total_stats = BatchStats(total_assets=len(assets))
        
        # Fetch common data first
        try:
            position_data = await fetch_position()
            ls_trend_data = await fetch_ls_trend()
            timestamp = position_data['lastUpdated']
            
            # Process global data
            global_position_data = process_global_position(position_data)
            processed_ls_trend_data = process_ls_trend(ls_trend_data)
        except Exception as e:
            logging.error(f"{Fore.RED}Error fetching/processing global data: {e}{Style.RESET_ALL}")
            total_stats.record_failure("GLOBAL", "fetch_global", str(e))
            return
        
        # Initialize InfluxDB writer
        influx_writer = InfluxWriter()
        
        # Process assets in batches
        for i in range(0, len(assets), batch_size):
            batch = assets[i:i + batch_size]
            batch_stats = BatchStats()
            logging.info(f"{Fore.CYAN}Processing batch {i//batch_size + 1}: {batch}{Style.RESET_ALL}")
            
            # Fetch data for batch concurrently
            asset_data_tasks = [fetch_asset_data(asset, circuit_breaker, batch_stats) for asset in batch]
            asset_data_results = await asyncio.gather(*asset_data_tasks)
            
            # Process batch data
            processed_data = []
            processed_liquidation_distribution = []
            
            for asset_data in asset_data_results:
                if asset_data:
                    batch_stats.successful_fetches += 1
                    result = await process_asset_data(asset_data, position_data, timestamp, circuit_breaker, batch_stats)
                    if result:
                        batch_stats.successful_processes += 1
                        if result.get('position'):
                            processed_data.append(result['position'])
                        if result.get('liquidation_distribution'):
                            processed_liquidation_distribution.append(result['liquidation_distribution'])
                    else:
                        batch_stats.failed_processes += 1
                else:
                    batch_stats.failed_fetches += 1
            
            # Validate batch data
            if processed_data:
                try:
                    validated_positions = validate_position_data(processed_data)
                    validated_liquidation_distribution = validate_liquidation_distribution_data(processed_liquidation_distribution)
                    batch_stats.successful_validations += len(validated_positions)
                    batch_stats.failed_validations += len(processed_data) - len(validated_positions)
                    
                    # Write batch to InfluxDB
                    if validated_positions:
                        try:
                            await write_to_influx(validated_positions, None)
                            batch_stats.successful_writes += len(validated_positions)
                        except Exception as e:
                            batch_stats.failed_writes += len(validated_positions)
                            for position in validated_positions:
                                batch_stats.record_failure(position.asset, "write", str(e))
                            logging.error(f"Error writing batch to InfluxDB: {e}")
                except Exception as e:
                    batch_stats.failed_validations += len(processed_data)
                    for data in processed_data:
                        batch_stats.record_failure(data.get('Asset', 'Unknown'), "validation", str(e))
                    logging.error(f"Error validating batch data: {e}")
            
            # Update total stats
            total_stats.successful_fetches += batch_stats.successful_fetches
            total_stats.failed_fetches += batch_stats.failed_fetches
            total_stats.successful_processes += batch_stats.successful_processes
            total_stats.failed_processes += batch_stats.failed_processes
            total_stats.successful_validations += batch_stats.successful_validations
            total_stats.failed_validations += batch_stats.failed_validations
            total_stats.successful_writes += batch_stats.successful_writes
            total_stats.failed_writes += batch_stats.failed_writes
            total_stats.failures.extend(batch_stats.failures)
            
            # Log batch stats with colors
            logging.info(f"""
                        {Fore.CYAN}Batch {i//batch_size + 1} Summary:{Style.RESET_ALL}
                        {Fore.GREEN}Successes:{Style.RESET_ALL}
                        Fetches: {batch_stats.successful_fetches}
                        Processing: {batch_stats.successful_processes}
                        Validations: {batch_stats.successful_validations}
                        Writes: {batch_stats.successful_writes}
                        {Fore.RED}Failures:{Style.RESET_ALL}
                        Fetches: {batch_stats.failed_fetches}
                        Processing: {batch_stats.failed_processes}
                        Validations: {batch_stats.failed_validations}
                        Writes: {batch_stats.failed_writes}
                        """)
            
            # Print detailed failures for this batch
            batch_stats.print_failures()
            
            # Clear batch data from memory
            del asset_data_results
            del processed_data
            del processed_liquidation_distribution
            gc.collect()
            
        # Process and write global data after all batches
        try:
            validated_global_position_data = validate_global_position_data(global_position_data)
            validated_ls_trend_data = validate_ls_trend_data(processed_ls_trend_data)
            
            # Write global data
            await write_to_influx(None, validated_global_position_data)
            
            # Log final stats with colors
            logging.info(f"""
                        {Fore.CYAN}Final Summary:{Style.RESET_ALL}
                        {Fore.GREEN}Total Successes:{Style.RESET_ALL}
                        Fetches: {total_stats.successful_fetches}
                        Processing: {total_stats.successful_processes}
                        Validations: {total_stats.successful_validations}
                        Writes: {total_stats.successful_writes}
                        {Fore.RED}Total Failures:{Style.RESET_ALL}
                        Fetches: {total_stats.failed_fetches}
                        Processing: {total_stats.failed_processes}
                        Validations: {total_stats.failed_validations}
                        Writes: {total_stats.failed_writes}
                        """)
            
            # Print all failures from all batches
            total_stats.print_failures()
            
        except Exception as e:
            logging.error(f"{Fore.RED}Error processing global data: {e}{Style.RESET_ALL}")
            total_stats.record_failure("GLOBAL", "process_global", str(e))
        
    except Exception as e:
        logging.error(f"{Fore.RED}Error in batch processing: {e}{Style.RESET_ALL}")
        raise

async def write_to_influx(validated_position_data, validated_global_position_data):
    """Write validated data to InfluxDB with improved error handling"""
    influx_writer = None
    try:
        influx_writer = InfluxWriter()
        
        if validated_position_data:
            for position in validated_position_data:
                try:
                    influx_writer.write_position_data([position])
                except Exception as e:
                    logging.error(f"Error writing position data for {position.asset}: {e}")
                    continue
            
        if validated_global_position_data:
            try:
                influx_writer.write_global_position(validated_global_position_data)
            except Exception as e:
                logging.error(f"Error writing global position data: {e}")
        
    except Exception as e:
        logging.error(f"Error writing to InfluxDB: {e}")
        raise
    finally:
        if influx_writer:
            influx_writer.close()

async def main():
    try:
        # Configure batch size based on available memory and asset count
        BATCH_SIZE = 5  # Adjust based on your system's capabilities
        
        # Fetch position data first to get crypto names
        try:
            position_data = await fetch_position()
            crypto_names = extract_crypto_names(position_data)
            
            if not crypto_names:
                logging.warning(f"{Fore.YELLOW}No crypto names found in position data, falling back to configured CRYPTO_NAMES{Style.RESET_ALL}")
                crypto_names = CRYPTO_NAMES
            else:
                logging.info(f"{Fore.GREEN}Found {len(crypto_names)} cryptocurrencies in position data{Style.RESET_ALL}")
                logging.info(f"Processing: {', '.join(crypto_names)}")
        except Exception as e:
            logging.error(f"{Fore.RED}Error fetching position data for crypto names, falling back to configured CRYPTO_NAMES: {e}{Style.RESET_ALL}")
            crypto_names = CRYPTO_NAMES
        
        # Start batch processing with dynamic crypto names
        await batch_process_assets(crypto_names, BATCH_SIZE)
        
    except Exception as e:
        logging.error(f"Application error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
    
