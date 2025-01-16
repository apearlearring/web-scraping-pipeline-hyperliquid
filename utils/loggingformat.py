import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List

from colorama import Fore, Style


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""

    COLOR_MAP = {
        logging.ERROR: Fore.RED,
        logging.WARNING: Fore.YELLOW,
        logging.INFO: Fore.WHITE
    }

    def format(self, record):
        # Add colors based on log level or content
        if record.levelno in self.COLOR_MAP:
            color = self.COLOR_MAP[record.levelno]
        elif "succeeded" in str(record.msg).lower():
            color = Fore.GREEN
        elif "failed" in str(record.msg).lower():
            color = Fore.RED
        else:
            color = Fore.WHITE

        record.msg = f"{color}{record.msg}{Style.RESET_ALL}"
        return super().format(record)


class LoggerSetup:
    """Handles all logging configuration and formatting"""

    @staticmethod
    def setup_logger() -> logging.Logger:
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            formatter = ColoredFormatter(
                '%(asctime)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            logger.addHandler(ch)

        return logger


@dataclass
class FailureRecord:
    """Records details of a failure during processing"""
    asset: str
    step: str
    error: str
    timestamp: datetime


@dataclass
class BatchStats:
    """Tracks statistics for batch processing"""
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
        """Record a failure with details"""
        self.failures.append(FailureRecord(
            asset=asset,
            step=step,
            error=str(error),
            timestamp=datetime.now()
        ))

    def print_failures(self):
        """Print formatted failure details"""
        if not self.failures:
            logging.info(f"{Fore.GREEN}No failures recorded{Style.RESET_ALL}")
            return

        logging.error("Failure Details:")
        for failure in self.failures:
            logging.error(f"{Fore.RED}Asset: {failure.asset}")
            logging.error(f"Step: {failure.step}")
            logging.error(f"Error: {failure.error}")
            logging.error(
                f"Time: {failure.timestamp.strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
            logging.error("-" * 50)

    def update_from_batch(self, other: 'BatchStats'):
        """Update stats from another BatchStats object"""
        self.successful_fetches += other.successful_fetches
        self.failed_fetches += other.failed_fetches
        self.successful_processes += other.successful_processes
        self.failed_processes += other.failed_processes
        self.successful_validations += other.successful_validations
        self.failed_validations += other.failed_validations
        self.successful_writes += other.successful_writes
        self.failed_writes += other.failed_writes
        self.failures.extend(other.failures)
