import logging
from typing import Dict, List

from config.settings import INFLUXDB_COMPRESSION_MIN_AGE

from .influx_base import InfluxBase


class InfluxReader(InfluxBase):
    """Reader class for querying data from InfluxDB with support for both raw and compressed data.

    This class provides methods to:
    - Read latest position data
    - Query historical asset data
    - Retrieve global market metrics
    - Automatically handle data source selection between raw and compressed buckets

    The reader automatically determines whether to read from the raw or compressed bucket
    based on the age of the data being queried.
    """

    def __init__(self):
        """Initialize the InfluxReader with query API setup."""
        super().__init__()
        self.query_api = self.client.query_api()

    def _get_bucket_for_timerange(self, hours: int) -> str:
        """Determine which bucket to read from based on data age.

        Args:
            hours (int): Number of hours of historical data requested

        Returns:
            str: Name of the bucket to read from (raw or compressed)
        """
        min_age_hours = int(INFLUXDB_COMPRESSION_MIN_AGE.rstrip('h'))
        return self.bucket if hours <= min_age_hours else self.compressed_bucket

    def get_latest_positions(self) -> List[Dict]:
        """Get the latest position data for all assets.

        Returns:
            List[Dict]: List of position data dictionaries, each containing:
                - asset: Asset symbol
                - total_notional: Total position value
                - ls_ratio: Long/Short ratio
                - current_price: Current asset price
                - traders_long: Number of long traders
                - traders_short: Number of short traders
                - timestamp: Data timestamp
        """
        # Always read latest data from raw bucket
        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: -24h)
          |> filter(fn: (r) => r["_measurement"] == "position_metrics")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> group(columns: ["asset"])
          |> last()
        '''

        try:
            result = self.query_api.query(query=query, org=self.org)
            positions = []

            for table in result:
                for record in table.records:
                    position = {
                        'asset': record.values.get('asset'),
                        'total_notional': record.values.get('total_notional'),
                        'ls_ratio': record.values.get('ls_ratio'),
                        'current_price': record.values.get('current_price'),
                        'traders_long': record.values.get('traders_long'),
                        'traders_short': record.values.get('traders_short'),
                        'timestamp': record.values.get('_time')
                    }
                    positions.append(position)

            return positions
        except Exception as e:
            logging.error(f"Error getting latest positions: {str(e)}")
            return []

    def get_asset_history(self, asset: str, hours: int = 24) -> List[Dict]:
        """Get historical position data for a specific asset.

        Args:
            asset (str): Asset symbol to query
            hours (int, optional): Number of hours of historical data to retrieve. Defaults to 24.

        Returns:
            List[Dict]: List of historical position data points, each containing:
                - timestamp: Data timestamp
                - total_notional: Total position value
                - ls_ratio: Long/Short ratio
                - current_price: Asset price at that time
        """
        bucket = self._get_bucket_for_timerange(hours)
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: -{hours}h)
          |> filter(fn: (r) => r["_measurement"] == "asset_positions")
          |> filter(fn: (r) => r["asset"] == "{asset}")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> sort(columns: ["_time"], desc: true)
        '''

        try:
            result = self.query_api.query(query=query, org=self.org)
            positions = []

            for table in result:
                for record in table.records:
                    position = {
                        'timestamp': record.values.get('_time'),
                        'total_notional': record.values.get('total_notional'),
                        'ls_ratio': record.values.get('ls_ratio'),
                        'current_price': record.values.get('current_price')
                    }
                    positions.append(position)

            return positions
        except Exception as e:
            logging.error(f"Error getting asset history for {asset}: {str(e)}")
            return []

    def get_global_metrics(self, hours: int = 24) -> List[Dict]:
        """Get historical global market metrics.

        Args:
            hours (int, optional): Number of hours of historical data to retrieve. Defaults to 24.

        Returns:
            List[Dict]: List of global metric data points, each containing:
                - timestamp: Data timestamp
                - total_notional_volume: Total market volume
                - global_ls_ratio: Global Long/Short ratio
                - long_positions_count: Number of long positions
                - short_positions_count: Number of short positions
        """
        bucket = self._get_bucket_for_timerange(hours)
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: -{hours}h)
          |> filter(fn: (r) => r["_measurement"] == "global_positions")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> sort(columns: ["_time"], desc: true)
        '''

        try:
            result = self.query_api.query(query=query, org=self.org)
            metrics = []

            for table in result:
                for record in table.records:
                    metric = {
                        'timestamp': record.values.get('_time'),
                        'total_notional_volume': record.values.get('total_notional_volume'),
                        'global_ls_ratio': record.values.get('global_ls_ratio'),
                        'long_positions_count': record.values.get('long_positions_count'),
                        'short_positions_count': record.values.get('short_positions_count')
                    }
                    metrics.append(metric)

            return metrics
        except Exception as e:
            logging.error(f"Error getting global metrics: {str(e)}")
            return []
