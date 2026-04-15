import logging
import sys
from src.config import LOG_FORMAT, LOG_LEVEL

def setup_logger(name):
    """Sets up a logger with a standard format and level."""
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if setup_logger is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(LOG_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, LOG_LEVEL))
        
    return logger
