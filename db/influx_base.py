import logging
from datetime import datetime

from influxdb_client import InfluxDBClient
from influxdb_client.client.tasks_api import TaskCreateRequest

from config.settings import (INFLUXDB_BUCKET, INFLUXDB_COMPRESSED_BUCKET,
                             INFLUXDB_COMPRESSED_RETENTION,
                             INFLUXDB_COMPRESSION_INTERVAL,
                             INFLUXDB_COMPRESSION_MIN_AGE,
                             INFLUXDB_DOWNSAMPLING_WINDOW, INFLUXDB_ORG,
                             INFLUXDB_RETENTION_PERIOD, INFLUXDB_TOKEN,
                             INFlUXDB_URL)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class InfluxBase:
    """Base class for InfluxDB operations with data retention and compression support.
    
    This class provides core functionality for:
    - Setting up and managing data retention policies
    - Configuring data compression and downsampling
    - Managing time-based data partitioning
    - Handling bucket creation and updates
    
    Attributes:
        DEFAULT_RETENTION_PERIOD (str): Default retention period for raw data
        COMPRESSED_RETENTION_PERIOD (str): Retention period for compressed data
        client (InfluxDBClient): InfluxDB client instance
        org (str): InfluxDB organization name
        bucket (str): Name of the raw data bucket
        compressed_bucket (str): Name of the compressed data bucket
    """
    
    DEFAULT_RETENTION_PERIOD = INFLUXDB_RETENTION_PERIOD
    COMPRESSED_RETENTION_PERIOD = INFLUXDB_COMPRESSED_RETENTION

    def __init__(self):
        self.client = InfluxDBClient(
            url=INFlUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        self.org = INFLUXDB_ORG
        self.bucket = INFLUXDB_BUCKET
        self.compressed_bucket = INFLUXDB_COMPRESSED_BUCKET
        print(f"\nInitializing InfluxDB connection to {INFlUXDB_URL}")
        self._setup_retention_policy()
        self._setup_compression_task()

    def _get_time_partition(self, timestamp) -> dict:
        """Get time-based partition components for better querying
        Returns components that can be used as tags for time-based partitioning
        """
        dt = datetime.fromisoformat(str(timestamp))
        return {
            "year": dt.strftime('%Y'),
            "month": dt.strftime('%m'),
            "day": dt.strftime('%d'),
            "hour": dt.strftime('%H')
        }

    def get_partitioned_measurement(self, base_name: str, _timestamp=None) -> str:
        """Get the measurement name without time suffix to reduce cardinality.
        
        Args:
            base_name (str): Base name for the measurement
            _timestamp: Unused parameter kept for backward compatibility
        
        Returns:
            str: The measurement name
        """
        return base_name

    def _setup_retention_policy(self):
        """Setup retention policies for both raw and compressed data"""
        try:
            buckets_api = self.client.buckets_api()

            # Setup raw data bucket
            raw_bucket = buckets_api.find_bucket_by_name(self.bucket)
            raw_retention_seconds = self._parse_duration(
                self.DEFAULT_RETENTION_PERIOD)
            raw_shard_duration = self._calculate_optimal_shard_duration(
                raw_retention_seconds)

            raw_retention_rule = {
                "type": "expire",
                "everySeconds": raw_retention_seconds,
                "shardGroupDurationSeconds": raw_shard_duration
            }

            # Setup compressed data bucket
            compressed_bucket = buckets_api.find_bucket_by_name(
                self.compressed_bucket)
            compressed_retention_seconds = self._parse_duration(
                self.COMPRESSED_RETENTION_PERIOD)
            compressed_shard_duration = self._calculate_optimal_shard_duration(
                compressed_retention_seconds)

            compressed_retention_rule = {
                "type": "expire",
                "everySeconds": compressed_retention_seconds,
                "shardGroupDurationSeconds": compressed_shard_duration
            }

            # Update or create raw data bucket
            if raw_bucket:
                raw_bucket.retention_rules = [raw_retention_rule]
                buckets_api.update_bucket(raw_bucket)
            else:
                buckets_api.create_bucket(
                    bucket_name=self.bucket,
                    org=self.org,
                    retention_rules=[raw_retention_rule]
                )

            # Update or create compressed data bucket
            if compressed_bucket:
                compressed_bucket.retention_rules = [compressed_retention_rule]
                buckets_api.update_bucket(compressed_bucket)
            else:
                buckets_api.create_bucket(
                    bucket_name=self.compressed_bucket,
                    org=self.org,
                    retention_rules=[compressed_retention_rule]
                )

            success_msg = (
                f"Setup retention policies:\n"
                f"  - Raw data: {self.DEFAULT_RETENTION_PERIOD}\n"
                f"  - Compressed data: {self.COMPRESSED_RETENTION_PERIOD}"
            )
            logging.info(success_msg)
            print(f"✓ {success_msg}")

        except Exception as e:
            error_msg = f"Error setting up retention policies: {e}"
            logging.error(error_msg)
            print(f"✗ {error_msg}")
            raise

    def _calculate_optimal_shard_duration(self, retention_seconds: int) -> int:
        """Calculate optimal shard group duration based on retention period.
        
        Args:
            retention_seconds (int): Retention period in seconds
            
        Returns:
            int: Optimal shard duration in seconds
        """
        hours_in_retention = retention_seconds / 3600

        if hours_in_retention <= 48:
            return 3600  # 1 hour
        if hours_in_retention <= 168:
            return 21600  # 6 hours
        if hours_in_retention <= 720:
            return 86400  # 1 day
        if hours_in_retention <= 4320:
            return 604800  # 7 days
        return 1209600  # 14 days

    def _parse_duration(self, duration_str: str) -> int:
        """Convert duration string to seconds.
        
        Args:
            duration_str (str): Duration string (e.g., '7d', '24h', '1w')
            
        Returns:
            int: Duration in seconds
        """
        unit = duration_str[-1]
        value = int(duration_str[:-1])

        if unit == 'd':
            return value * 24 * 60 * 60
        if unit == 'w':
            return value * 7 * 24 * 60 * 60
        if unit == 'h':
            return value * 60 * 60
        return value  # Assume seconds if no unit matches

    def _setup_compression_task(self):
        """Setup task for data compression and downsampling"""
        try:
            tasks_api = self.client.tasks_api()

            # Define the Flux query for downsampling
            flux_query = f'''
            option task = {{
                name: "compress_historical_data",
                every: {INFLUXDB_COMPRESSION_INTERVAL}
            }}

            // Process position metrics
            from(bucket: "{self.bucket}")
                |> range(start: -{INFLUXDB_COMPRESSION_MIN_AGE})
                |> filter(fn: (r) => r["_measurement"] == "asset_positions")
                |> aggregateWindow(
                    every: {INFLUXDB_DOWNSAMPLING_WINDOW},
                    fn: mean,
                    createEmpty: false
                )
                |> to(bucket: "{self.compressed_bucket}", org: "{self.org}")

            // Process global metrics
            from(bucket: "{self.bucket}")
                |> range(start: -{INFLUXDB_COMPRESSION_MIN_AGE})
                |> filter(fn: (r) => r["_measurement"] == "global_positions")
                |> aggregateWindow(
                    every: {INFLUXDB_DOWNSAMPLING_WINDOW},
                    fn: mean,
                    createEmpty: false
                )
                |> to(bucket: "{self.compressed_bucket}", org: "{self.org}")
            '''

            # Check if task already exists
            tasks = tasks_api.find_tasks()
            compression_task = next(
                (task for task in tasks if task.name == "compress_historical_data"),
                None
            )

            if compression_task:
                # Update existing task
                compression_task.flux = flux_query
                compression_task.description = "Compress and downsample historical data"
                compression_task.status = "active"
                tasks_api.update_task(compression_task)
                success_msg = "Updated data compression task"
            else:
                # Create new task
                task_request = TaskCreateRequest(
                    org_id=self.org,
                    flux=flux_query,
                    description="Compress and downsample historical data",
                    status="active"
                )
                tasks_api.create_task(task_request)
                success_msg = "Created data compression task"

            logging.info(success_msg)
            print(f"✓ {success_msg}")

        except Exception as e:
            error_msg = f"Error setting up compression task: {str(e)}"
            logging.error(error_msg)
            print(f"✗ {error_msg}")
            # Don't raise the exception - compression is optional
            # The system can still function with raw data only

    def close(self):
        """Close the InfluxDB client"""
        self.client.close()
