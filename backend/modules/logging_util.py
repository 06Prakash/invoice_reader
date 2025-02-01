from logging.handlers import RotatingFileHandler
import logging
import os
from datetime import datetime, timedelta

LOG_FILE_PATH = '/app/logs/app.log'  # Main log file
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 15  # Keep up to 15 backup log files
LOG_RETENTION_DAYS = 2  # Retain logs for 2 days

class CustomRotatingFileHandler(RotatingFileHandler):
    def rotation_filename(self, default_name):
        """
        Customize the naming of rotated log files.
        Example: applog_1.log, applog_2.log, etc.
        """
        # Extract base name and extension
        base_name, ext = os.path.splitext(self.baseFilename)
        # Get the suffix from the default_name
        suffix = default_name.replace(self.baseFilename, "").lstrip(".")
        # Add an underscore before the numeric part
        return f"{base_name}_{suffix}{ext}"

class ContextFilter(logging.Filter):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def filter(self, record):
        record.source_file = self.filename
        return True

def setup_logger(source_file):
    """Set up a logger with the source file as context."""
    # Ensure the log directory exists
    log_dir = os.path.dirname(LOG_FILE_PATH)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("ApplicationLogger")
    logger.setLevel(getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO))

    # Prevent duplicate handlers for the same logger
    if not logger.handlers:
        # Use the custom RotatingFileHandler for customized log file naming
        rotating_handler = CustomRotatingFileHandler(
            LOG_FILE_PATH,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
        )
        rotating_handler.setLevel(getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO))

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(source_file)s:%(lineno)d] - %(message)s')
        rotating_handler.setFormatter(formatter)

        logger.addHandler(rotating_handler)

    # Add a filter to inject the source file into the log records
    logger.addFilter(ContextFilter(source_file))
    return logger

def cleanup_old_logs():
    """Remove log files older than LOG_RETENTION_DAYS."""
    cutoff_date = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)
    for filename in os.listdir(os.path.dirname(LOG_FILE_PATH)):
        file_path = os.path.join(os.path.dirname(LOG_FILE_PATH), filename)
        if os.path.isfile(file_path):
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_mod_time < cutoff_date:
                os.remove(file_path)
                logging.getLogger("ApplicationLogger").info(f"Deleted old log file: {file_path}")

# Log uncaught exceptions
def log_uncaught_exceptions(exc_type, exc_value, exc_traceback):
    logger = logging.getLogger("ApplicationLogger")
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

import sys
sys.excepthook = log_uncaught_exceptions
