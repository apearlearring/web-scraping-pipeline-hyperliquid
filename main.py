import asyncio
from process import *
from config.settings import CRYPTO_NAMES
from colorama import init, Fore, Style
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
                logger.warning(f"{Fore.YELLOW}No crypto names found in position data, falling back to configured CRYPTO_NAMES{Style.RESET_ALL}")
                crypto_names = CRYPTO_NAMES
            else:
                logger.info(f"{Fore.GREEN}Found {len(crypto_names)} cryptocurrencies in position data{Style.RESET_ALL}")
                logger.info(f"Processing: {', '.join(crypto_names)}")
        except Exception as e:
            logger.error(f"{Fore.RED}Error fetching position data for crypto names, falling back to configured CRYPTO_NAMES: {e}{Style.RESET_ALL}")
            crypto_names = CRYPTO_NAMES
        
        # Initialize and run batch processor
        batch_processor = BatchProcessor(batch_size=5)
        await batch_processor.process_batches(crypto_names)
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
    
