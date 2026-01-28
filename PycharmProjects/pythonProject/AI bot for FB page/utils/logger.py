"""
Logger configuration for the application.
"""

from loguru import logger
import sys
from pathlib import Path


def setup_logger(log_level: str = "INFO", log_dir: str = "logs"):
    """
    Configure loguru logger.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files
    """
    # Remove default handler
    logger.remove()

    # Console handler with colors
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level=log_level,
        colorize=True
    )

    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # File handler for all logs
    logger.add(
        log_path / "app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )

    # File handler for errors only
    logger.add(
        log_path / "errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="1 day",
        retention="90 days",
        compression="zip"
    )

    # File handler for rate limits
    logger.add(
        log_path / "rate_limits.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        level="WARNING",
        filter=lambda record: "rate" in record["message"].lower(),
        rotation="1 day",
        retention="30 days"
    )

    return logger


def get_logger():
    """Get the configured logger instance."""
    return logger
