import logging
from datetime import datetime
from typing import List

from influxdb_client import Point
from influxdb_client.client.write_api import SYNCHRONOUS

from .influx_base import InfluxBase


class InfluxWriter(InfluxBase):
    def __init__(self):
        super().__init__()
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def write_position_data(self, positions: List):
        """Write position data to InfluxDB with optimized partitioning"""
        try:
            for position in positions:
                # Get base measurement name (without time suffix)
                measurement_name = self.get_partitioned_measurement(
                    "asset_positions", position.timestamp)
                # Get time partition tags
                time_tags = self._get_time_partition(position.timestamp)

                point = (
                    Point(measurement_name)
                    # Time-based partition tags
                    .tag("year", time_tags["year"])
                    .tag("month", time_tags["month"])
                    .tag("day", time_tags["day"])
                    # Business tags
                    .tag("asset", position.asset)
                    .tag("majority_side", position.majority_side)
                    .tag("minority_side", position.minority_side)
                    .tag("majority_pnl_status", position.majority_pnl_status)
                    .tag("minority_pnl_status", position.minority_pnl_status)
                    .tag("base_currency", position.base_currency)
                    .tag('liquidation_time_window', position.liquidation_metrics.time_window)
                    # Fields remain the same
                    .field("total_notional", float(position.total_notional))
                    .field("ls_ratio", float(position.ls_ratio))
                    .field("majority_notional", float(position.majority_notional))
                    .field("majority_entry_price", float(position.majority_entry_price))
                    .field("minority_notional", float(position.minority_notional))
                    .field("minority_entry_price", float(position.minority_entry_price))
                    .field("current_price", float(position.current_price))
                    .field("traders_long", position.traders_long)
                    .field("traders_short", position.traders_short)
                    .field("open_interest", float(position.open_interest))
                    .field("open_interest_coverage", float(position.open_interest_coverage))
                    .field("funding_history", float(position.funding_history.rate))
                    .field("liquidation_total_volume", float(position.liquidation_metrics.total_volume))
                    .field("liquidation_largest_single", float(position.liquidation_metrics.largest_single))
                    .field("liquidation_long_volume", float(position.liquidation_metrics.long_volume))
                    .field("liquidation_short_volume", float(position.liquidation_metrics.short_volume))
                    .time(datetime.fromisoformat(str(position.timestamp)))
                )
                self.write_api.write(bucket=self.bucket, record=point)
                logging.info(
                    f"Successfully wrote position data for {
                        position.asset} to {measurement_name} [{
                        time_tags['year']}-{
                        time_tags['month']}-{
                        time_tags['day']}]")
                print(
                    f"✓ Wrote position data: {
                        position.asset} -> {measurement_name} [{
                        time_tags['year']}-{
                        time_tags['month']}-{
                        time_tags['day']}]")
        except Exception as e:
            error_msg = f"Error writing position data: {e}"
            logging.error(error_msg)
            print(f"✗ {error_msg}")
            raise

    def write_global_position(self, global_data):
        """Write global position data to InfluxDB with daily partitioning"""
        try:
            measurement_name = self.get_partitioned_measurement(
                "global_positions", global_data.timestamp)
            point = (
                Point(measurement_name)
                .field("total_notional_volume", float(global_data.total_notional_volume))
                .field("total_tickers", global_data.total_tickers)
                .field("long_positions_count", float(global_data.long_positions_count))
                .field("short_positions_count", float(global_data.short_positions_count))
                .field("global_ls_ratio", float(global_data.global_ls_ratio))
                .time(datetime.fromisoformat(str(global_data.timestamp)))
            )
            self.write_api.write(bucket=self.bucket, record=point)
            print(point)
            logging.info(
                f"Successfully wrote global position data to measurement {measurement_name}")
            print(f"✓ Wrote global position data -> {measurement_name}")
        except Exception as e:
            error_msg = f"Error writing global position data: {e}"
            logging.error(error_msg)
            print(f"✗ {error_msg}")
            raise