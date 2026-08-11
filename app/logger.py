import sys
from loguru import logger


def setup_logger():
    # Remove default logger
    logger.remove()

    # Console logger — human readable during development
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{line} | {message}",
        level="DEBUG",
        colorize=True
    )

    # File logger — saved to disk for production
    logger.add(
        "logs/app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{line} | {message}",
        level="INFO",
        rotation="10 MB",    # new file when this one hits 10MB
        retention="30 days", # delete logs older than 30 days
        compression="zip"    # compress old log files
    )

    return logger
