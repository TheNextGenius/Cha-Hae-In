import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from config import LOG_LEVEL, LOG_FILE

def setup_logger():
    """Configure logging system"""
    logger = logging.getLogger('cha_hae_in')
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (rotating by size)
    try:
        os.makedirs('logs', exist_ok=True)
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=5*1024*1024,  # 5 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.error(f"Failed to setup file logging: {e}")

    return logger
