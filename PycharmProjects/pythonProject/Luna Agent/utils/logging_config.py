"""Centralized logging configuration for Luna CLI.

This module configures logging to:
1. Keep the console clean (only WARNING+ from Luna's own modules)
2. Route verbose DEBUG/INFO logs from httpx, google_genai to files
3. Implement log rotation to prevent disk space issues
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Define logs directory
LOGS_DIR = Path(__file__).parent.parent / "logs"

# Verbose libraries that should only log to file (not console)
VERBOSE_LOGGERS = [
    "httpx",
    "httpcore", 
    "google_genai",
    "google.genai",
    "google.auth",
    "google.api_core",
    "urllib3",
    "chromadb",
    "sentence_transformers",
    "transformers",
    "huggingface_hub",
]


def setup_logging(
    console_level: int = logging.WARNING,
    file_level: int = logging.DEBUG,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> None:
    """
    Configure logging for Luna CLI with clean console output.
    
    Args:
        console_level: Minimum level for console output (default: WARNING)
        file_level: Minimum level for file output (default: DEBUG)
        log_format: Format string for log messages
    """
    # Create logs directory
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything, filter at handler level
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # === FILE HANDLER (captures everything for debugging) ===
    file_handler = RotatingFileHandler(
        LOGS_DIR / "luna_debug.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S"))
    root_logger.addHandler(file_handler)
    
    # === CONSOLE HANDLER (clean output for chat experience) ===
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(logging.Formatter("%(message)s"))  # Minimal format
    root_logger.addHandler(console_handler)
    
    # === SILENCE VERBOSE LIBRARIES ON CONSOLE ===
    # These libraries will still log to file but not clutter the console
    for logger_name in VERBOSE_LOGGERS:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)  # Only show warnings/errors in console
        # Ensure they don't propagate to root (which has console handler)
        # But we still want them in the file, so we add file handler directly
        logger.handlers.clear()
        logger.addHandler(file_handler)
        logger.propagate = False  # Don't propagate to root logger's console


# Auto-configure on import
setup_logging()
