from typing import Dict, List

from .influx_base import InfluxBase


class InfluxReader(InfluxBase):
    def __init__(self):
        super().__init__()
        self.query_api = self.client.query_api()

    def get_latest_positions(self) -> List[Dict]:
        """Get the latest position data for all assets"""
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
            print(f"Error getting latest positions: {e}")
            return []

    def get_asset_history(self, asset: str, hours: int = 24) -> List[Dict]:
        """Get historical position data for a specific asset"""
        query = f'''
        from(bucket: "{self.bucket}")
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
            print(f"Error getting asset history: {e}")
            return []

    def get_global_metrics(self, hours: int = 24) -> List[Dict]:
        """Get historical global metrics"""
        query = f'''
        from(bucket: "{self.bucket}")
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
            print(f"Error getting global metrics: {e}")
            return []