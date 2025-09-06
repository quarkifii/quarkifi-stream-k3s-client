import logging
from logging.handlers import RotatingFileHandler
import os

home_dir = os.getenv("K3S_THIN_CLIENT_HOME")
log_file = os.path.join(home_dir, 'logs', 'qstream-k3s-client.log')

def get_logger(name: str, log_file: str = log_file, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # Rotating handler: 1MB per file, keep 5 backups
        handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3)
        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger