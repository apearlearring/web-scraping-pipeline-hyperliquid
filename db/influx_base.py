from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from config.settings import (
    INFLUXDB_TOKEN,
    INFLUXDB_ORG,
    INFLUXDB_BUCKET,
    INFlUXDB_URL,
    INFLUXDB_RETENTION_PERIOD
)
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class InfluxBase:
    DEFAULT_RETENTION_PERIOD = INFLUXDB_RETENTION_PERIOD

    def __init__(self):
        self.client = InfluxDBClient(
            url=INFlUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        self.org = INFLUXDB_ORG
        self.bucket = INFLUXDB_BUCKET
        print(f"\nInitializing InfluxDB connection to {INFlUXDB_URL}")
        self._setup_retention_policy()

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

    def get_partitioned_measurement(self, base_name: str, timestamp) -> str:
        """Get the measurement name without time suffix to reduce cardinality
        Time partitioning is handled through tags instead of measurement names
        """
        return base_name

    def _setup_retention_policy(self):
        """Setup retention policy for the bucket to automatically remove old data"""
        try:
            buckets_api = self.client.buckets_api()
            bucket = buckets_api.find_bucket_by_name(self.bucket)
            retention_seconds = self._parse_duration(self.DEFAULT_RETENTION_PERIOD)

            # Optimize shard group duration based on retention period
            shard_duration = self._calculate_optimal_shard_duration(retention_seconds)

            retention_rule = {
                "type": "expire",
                "everySeconds": retention_seconds,
                "shardGroupDurationSeconds": shard_duration
            }
            
            if bucket:
                bucket.retention_rules = [retention_rule]
                buckets_api.update_bucket(bucket)
                success_msg = (
                    f"Updated retention policy: data older than {self.DEFAULT_RETENTION_PERIOD} "
                    f"will be automatically removed (shard duration: {shard_duration//3600}h)"
                )
                logging.info(success_msg)
                print(f"✓ {success_msg}")
            else:
                buckets_api.create_bucket(
                    bucket_name=self.bucket,
                    org=self.org,
                    retention_rules=[retention_rule]
                )
                success_msg = (
                    f"Created bucket with retention policy: data older than {self.DEFAULT_RETENTION_PERIOD} "
                    f"will be automatically removed (shard duration: {shard_duration//3600}h)"
                )
                logging.info(success_msg)
                print(f"✓ {success_msg}")

        except Exception as e:
            error_msg = f"Error setting up retention policy: {e}"
            logging.error(error_msg)
            print(f"✗ {error_msg}")
            raise

    def _calculate_optimal_shard_duration(self, retention_seconds: int) -> int:
        """Calculate optimal shard group duration based on retention period"""
        # InfluxDB best practices for shard group duration:
        # - Retention period < 2 days: 1h shard duration
        # - Retention period < 7 days: 6h shard duration
        # - Retention period < 30 days: 1d shard duration
        # - Retention period < 180 days: 7d shard duration
        # - Retention period >= 180 days: 14d shard duration
        hours_in_retention = retention_seconds / 3600
        
        if hours_in_retention <= 48:
            return 3600  # 1 hour
        elif hours_in_retention <= 168:
            return 21600  # 6 hours
        elif hours_in_retention <= 720:
            return 86400  # 1 day
        elif hours_in_retention <= 4320:
            return 604800  # 7 days
        else:
            return 1209600  # 14 days

    def _parse_duration(self, duration_str: str) -> int:
        """Convert duration string to seconds"""
        unit = duration_str[-1]
        value = int(duration_str[:-1])
        
        if unit == 'd':
            return value * 24 * 60 * 60
        elif unit == 'w':
            return value * 7 * 24 * 60 * 60
        elif unit == 'h':
            return value * 60 * 60
        return value

    def close(self):
        """Close the InfluxDB client"""
        self.client.close() 