# utils/logger_setup.py
"""
Logger Setup Utility
Configures logging for the application
"""

import logging
from typing import Optional


def setup_logger(
    name: str = "app",
    level: int = logging.DEBUG,
    console_format: str = '[%(asctime)s] [%(levelname)s] %(message)s',
    date_format: str = '%d/%m %H:%M:%S'
) -> logging.Logger:
    """
    Set up logging configuration for console output.
    
    Args:
        name: Logger name
        level: Logging level
        console_format: Format string for console output
        date_format: Date format string
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(console_format, date_format)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger