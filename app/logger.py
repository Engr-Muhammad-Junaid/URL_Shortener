import os
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

    # Vercel functions have a read-only application filesystem and collect
    # stdout automatically. Local and Docker deployments retain file logs.
    if not os.getenv("VERCEL"):
        logger.add(
            "logs/app.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{line} | {message}",
            level="INFO",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
        )

    return logger
