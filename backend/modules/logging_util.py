import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime, timedelta

LOG_DIR = '/app/logs/'
LOG_FILE = os.path.join(LOG_DIR, 'app.log')
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 15  # Keep up to 5 backup log files
LOG_RETENTION_DAYS = 60  # Retain logs for 2 months

def setup_logger():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Rotating File Handler
    rotating_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT
    )
    rotating_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    rotating_handler.setFormatter(formatter)

    logger.addHandler(rotating_handler)
    return logger

def cleanup_old_logs():
    """Remove log files older than LOG_RETENTION_DAYS."""
    cutoff_date = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)
    for filename in os.listdir(LOG_DIR):
        file_path = os.path.join(LOG_DIR, filename)
        if os.path.isfile(file_path):
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_mod_time < cutoff_date:
                os.remove(file_path)
                print(f"Deleted old log file: {file_path}")