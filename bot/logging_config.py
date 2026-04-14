import logging
import sys
from pathlib import Path

def setup_logging(log_file: str = "trading_bot.log"):
    """Sets up logging to both file and console."""
    log_path = Path(log_file)
    
    # Create logger
    logger = logging.getLogger("trading_bot")
    logger.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-7s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Optional: Log a separator to mark a new execution session
    logger.info("="*60)
    logger.info(" NEW TRADING SESSION STARTED ".center(60, "="))
    logger.info("="*60)
    
    # File handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Console handler (optional, Rich will handle main CLI output but we keep this for debug)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    # logger.addHandler(console_handler) # Rich handles console, so maybe keep this disabled or at high level
    
    return logger

logger = setup_logging()
