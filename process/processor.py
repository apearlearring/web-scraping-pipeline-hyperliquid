from typing import Optional, Tuple

from db import write_to_influx
from fetch import *
from process import process_funding_history, process_liquidation, process_position, process_global_position, process_ls_trend
from utils import *
from validate import *


class DataProcessor:
    """Handles all data processing operations"""

    def __init__(self):
        self.circuit_breaker = CircuitBreaker()
        self.logger = logging.getLogger()

    async def fetch_asset_data(self, asset: str,
                               batch_stats: BatchStats) -> Optional[Dict]:
        """Fetch all data for a single asset concurrently with circuit breaker"""
        operation_key = f"fetch_{asset}"
        if not self.circuit_breaker.can_proceed(operation_key):
            self.logger.warning(
                f"Circuit breaker open for {asset}, skipping fetch")
            batch_stats.record_failure(asset, "fetch", "Circuit breaker open")
            return None

        try:
            liquidation_data, funding_history = await asyncio.gather(
                fetch_liquidation(asset),
                fetch_funding_history(asset)
            )

            if liquidation_data is None and funding_history is None:
                self.circuit_breaker.record_failure(operation_key)
                batch_stats.record_failure(
                    asset, "fetch", "Both liquidation and funding data are None")
                return None

            result = {
                'asset': asset,
                'liquidation_data': liquidation_data,
                'funding_history': funding_history
            }

            self.circuit_breaker.record_success(operation_key)
            return result
        except Exception as e:
            self.circuit_breaker.record_failure(operation_key)
            batch_stats.record_failure(asset, "fetch", str(e))
            self.logger.error(f"Error fetching data for {asset}: {e}")
            return None

    async def process_asset_data(self, asset_data: Dict, position_data: Dict,
                                 timestamp: str, batch_stats: BatchStats) -> Optional[Dict]:
        """Process data for a single asset with partial result handling"""
        if not asset_data:
            return None

        asset = asset_data['asset']
        operation_key = f"process_{asset}"

        if not self.circuit_breaker.can_proceed(operation_key):
            self.logger.warning(
                f"Circuit breaker open for processing {asset}, skipping")
            batch_stats.record_failure(
                asset, "process", "Circuit breaker open")
            return None

        try:
            result = await self._process_components(asset_data, position_data, timestamp, asset, batch_stats)
            if result:
                self.circuit_breaker.record_success(operation_key)
                return result

            self.circuit_breaker.record_failure(operation_key)
            batch_stats.record_failure(
                asset, "process", "No valid data to process")
            return None

        except Exception as e:
            self.circuit_breaker.record_failure(operation_key)
            batch_stats.record_failure(asset, "process", str(e))
            self.logger.error(f"Error processing data for {asset}: {e}")
            return None

    async def _process_components(self, asset_data: Dict, position_data: Dict,
                                  timestamp: str, asset: str, batch_stats: BatchStats) -> Optional[Dict]:
        """Process individual components of asset data"""
        result = {}

        # Process funding history
        try:
            result['funding_history'] = self._process_funding(
                asset_data, asset, batch_stats)
        except Exception as e:
            self.logger.error(
                f"{asset}: Error processing funding history: {e}")
            batch_stats.record_failure(asset, "process_funding", str(e))

        # Process position data
        try:
            result['position_data'] = self._process_position(
                position_data, asset, batch_stats)
        except Exception as e:
            self.logger.error(f"{asset}: Error processing position data: {e}")
            batch_stats.record_failure(asset, "process_position", str(e))

        # Process liquidation data
        try:
            liquidation_result = self._process_liquidation(
                asset_data, asset, batch_stats)
            if liquidation_result:
                result.update(liquidation_result)
        except Exception as e:
            self.logger.error(
                f"{asset}: Error processing liquidation data: {e}")
            batch_stats.record_failure(asset, "process_liquidation", str(e))

        # Final position processing
        if any(result.values()):
            try:
                return self._process_final_position(
                    result, timestamp, asset, batch_stats)
            except Exception as e:
                self.logger.error(
                    f"{asset}: Error in final position processing: {e}")
                batch_stats.record_failure(asset, "process_final", str(e))

        return None

    def _process_funding(self, asset_data: Dict, asset: str,
                         batch_stats: BatchStats) -> Optional[float]:
        """Process funding history data"""
        if asset_data['funding_history']:
            return process_funding_history(asset_data['funding_history'][-1])
        return None

    def _process_position(self, position_data: Dict, asset: str,
                          batch_stats: BatchStats) -> Optional[Dict]:
        """Process position data"""
        return next(
            (data for data in position_data['data'] if data['Asset'] == asset),
            None
        )

    def _process_liquidation(
            self, asset_data: Dict, asset: str, batch_stats: BatchStats) -> Optional[Dict]:
        """Process liquidation data"""
        if asset_data['liquidation_data']:
            metrics, distribution = process_liquidation(
                liquidation_data=asset_data['liquidation_data'],
                asset_name=asset
            )
            return {
                'liquidation_metrics': metrics,
                'liquidation_distribution': distribution
            }
        return None

    def _process_final_position(self, result: Dict, timestamp: str,
                                asset: str, batch_stats: BatchStats) -> Optional[Dict]:
        """Process final position data"""
        processed_position = process_position(
            position_data=result.get('position_data'),
            funding_history=result.get('funding_history'),
            liquidation_metrics=result.get('liquidation_metrics'),
            lastupdated=timestamp
        )

        return {
            'position': processed_position,
            'liquidation_distribution': result.get('liquidation_distribution')
        }


class BatchProcessor:
    """Handles batch processing of assets"""

    def __init__(self, batch_size: int = 5):
        self.batch_size = batch_size
        self.data_processor = DataProcessor()
        self.logger = logging.getLogger()

    async def process_batches(self, assets: List[str]) -> None:
        """Process assets in batches"""
        total_stats = BatchStats(total_assets=len(assets))

        try:
            # Get common data
            position_data, ls_trend_data = await self._fetch_common_data(total_stats)
            if not position_data:
                return

            # Process batches
            await self._process_asset_batches(assets, position_data, total_stats)

            # Process global data
            await self._process_global_data(position_data, ls_trend_data, total_stats)

        except Exception as e:
            self.logger.error(
                f"{Fore.RED}Error in batch processing: {e}{Style.RESET_ALL}")
            raise

    async def _fetch_common_data(
            self, total_stats: BatchStats) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Fetch common data needed for processing"""
        try:
            position_data = await fetch_position()
            ls_trend_data = await fetch_ls_trend()
            return position_data, ls_trend_data
        except Exception as e:
            self.logger.error(
                f"{Fore.RED}Error fetching common data: {e}{Style.RESET_ALL}")
            total_stats.record_failure("GLOBAL", "fetch_common", str(e))
            return None, None

    async def _process_global_data(
            self, position_data: Dict, ls_trend_data: Dict, total_stats: BatchStats) -> None:
        """Process and write global market data"""
        try:
            # Process global data
            global_position_data = process_global_position(position_data)
            processed_ls_trend_data = process_ls_trend(ls_trend_data)

            # Validate global data
            validated_global_position_data = validate_global_position_data(
                global_position_data)
            validated_ls_trend_data = validate_ls_trend_data(
                processed_ls_trend_data)

            # Write global data to InfluxDB
            await write_to_influx(None, validated_global_position_data)

            # Log final stats
            self.logger.info(f"""
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
            self.logger.error(
                f"{Fore.RED}Error processing global data: {e}{Style.RESET_ALL}")
            total_stats.record_failure("GLOBAL", "process_global", str(e))

    async def _process_asset_batches(
            self, assets: List[str], position_data: Dict, total_stats: BatchStats) -> None:
        """Process assets in batches"""
        for i in range(0, len(assets), self.batch_size):
            batch = assets[i:i + self.batch_size]
            batch_stats = await self._process_single_batch(batch, position_data, i)
            total_stats.update_from_batch(batch_stats)

    async def _process_single_batch(
            self, batch: List[str], position_data: Dict, batch_index: int) -> BatchStats:
        """Process a single batch of assets"""
        batch_stats = BatchStats()
        self.logger.info(
            f"{Fore.CYAN}Processing batch {batch_index + 1}: {batch}{Style.RESET_ALL}")

        # Fetch and process batch data
        results = await self._fetch_and_process_batch(batch, position_data, batch_stats)

        # Validate and write results
        await self._validate_and_write_batch(results, batch_stats)

        # Log batch results
        self._log_batch_results(batch_stats, batch_index)

        return batch_stats

    async def _fetch_and_process_batch(
            self, batch: List[str], position_data: Dict, batch_stats: BatchStats) -> Tuple[List, List]:
        """Fetch and process a batch of assets"""
        processed_data = []
        processed_liquidation_distribution = []

        # Fetch data concurrently
        asset_data_tasks = [
            self.data_processor.fetch_asset_data(
                asset, batch_stats) for asset in batch]
        asset_data_results = await asyncio.gather(*asset_data_tasks)

        # Process results
        timestamp = position_data['lastUpdated']
        for asset_data in asset_data_results:
            if asset_data:
                batch_stats.successful_fetches += 1
                result = await self.data_processor.process_asset_data(asset_data, position_data, timestamp, batch_stats)
                if result:
                    batch_stats.successful_processes += 1
                    if result.get('position'):
                        processed_data.append(result['position'])
                    if result.get('liquidation_distribution'):
                        processed_liquidation_distribution.append(
                            result['liquidation_distribution'])
                else:
                    batch_stats.failed_processes += 1
            else:
                batch_stats.failed_fetches += 1

        return processed_data, processed_liquidation_distribution

    async def _validate_and_write_batch(
            self, results: Tuple[List, List], batch_stats: BatchStats) -> None:
        """Validate and write batch results"""
        processed_data, processed_liquidation_distribution = results

        if not processed_data:
            return

        try:
            # Validate data
            validated_positions = validate_position_data(processed_data)
            validated_liquidation_distribution = validate_liquidation_distribution_data(
                processed_liquidation_distribution)

            batch_stats.successful_validations += len(validated_positions)
            batch_stats.failed_validations += len(
                processed_data) - len(validated_positions)

            # Write to InfluxDB
            if validated_positions:
                await self._write_batch_to_influx(validated_positions, batch_stats)

        except Exception as e:
            batch_stats.failed_validations += len(processed_data)
            for data in processed_data:
                batch_stats.record_failure(
                    data.get(
                        'Asset',
                        'Unknown'),
                    "validation",
                    str(e))
            self.logger.error(f"Error validating batch data: {e}")

    async def _write_batch_to_influx(
            self, validated_positions: List, batch_stats: BatchStats) -> None:
        """Write batch data to InfluxDB"""
        try:
            await write_to_influx(validated_positions, None)
            batch_stats.successful_writes += len(validated_positions)
        except Exception as e:
            batch_stats.failed_writes += len(validated_positions)
            for position in validated_positions:
                batch_stats.record_failure(position.asset, "write", str(e))
            self.logger.error(f"Error writing batch to InfluxDB: {e}")

    def _log_batch_results(self, batch_stats: BatchStats,
                           batch_index: int) -> None:
        """Log batch processing results"""
        self.logger.info(f"""
{Fore.CYAN}Batch {batch_index + 1} Summary:{Style.RESET_ALL}
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
        batch_stats.print_failures()
