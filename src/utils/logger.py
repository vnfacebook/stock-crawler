from loguru import logger
import sys
import os

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)
logger.add(
    "logs/crawler.log",
    rotation="10 MB",
    retention="1 week",
    compression="zip",
    level="DEBUG",
)
