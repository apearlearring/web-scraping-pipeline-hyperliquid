import asyncio

from colorama import Fore, Style, init

from config.settings import CRYPTO_NAMES
from db import read_from_influx
from process import *
from utils import extract_crypto_names

# Initialize colorama for Windows
init()


async def main():
    """Main entry point of the application"""
    # Setup logging
    logger = LoggerSetup.setup_logger()

    try:
        # Get crypto names from position data
        try:
            position_data = await fetch_position()
            crypto_names = extract_crypto_names(position_data)

            if not crypto_names:
                logger.warning(
                    f"{
                        Fore.YELLOW}No crypto names found in position data, falling back to configured CRYPTO_NAMES{
                        Style.RESET_ALL}")
                crypto_names = CRYPTO_NAMES
            else:
                logger.info(
                    f"{
                        Fore.GREEN}Found {
                        len(crypto_names)} cryptocurrencies in position data{
                        Style.RESET_ALL}")
                logger.info(f"Processing: {', '.join(crypto_names)}")
        except Exception as e:
            logger.error(
                f"{
                    Fore.RED}Error fetching position data for crypto names, falling back to configured CRYPTO_NAMES: {e}{
                    Style.RESET_ALL}")
            crypto_names = CRYPTO_NAMES

        # Initialize and run batch processor
        batch_processor = BatchProcessor(batch_size=5)
        await batch_processor.process_batches(crypto_names)

    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


def show_db(data_type: str = 'global_metrics',
            asset: str = "BTC", hours: int = 24):
    """Display database contents using the read_from_influx function.

    Args:
        data_type (str): Type of data to read ('latest_positions', 'asset_history', 'global_metrics')
        asset (str, optional): Asset symbol for asset-specific queries. Required for 'asset_history'.
        hours (int): Number of hours of historical data to retrieve
    """
    try:
        read_from_influx(data_type=data_type, asset=asset, hours=hours)
    except (ConnectionError, TimeoutError) as e:
        print(f"{Fore.RED}Database connection error: {e}{Style.RESET_ALL}")
    except ValueError as e:
        print(f"{Fore.RED}Invalid input parameters: {e}{Style.RESET_ALL}")


if __name__ == "__main__":
    asyncio.run(main())
    # show_db()
