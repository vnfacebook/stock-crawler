from abc import ABC, abstractmethod
from typing import Any, List, Dict
import time
import random
from src.utils.logger import logger

class BaseCrawler(ABC):
    SOURCE_NAME: str = ""
    BASE_URL: str = ""

    def __init__(self, delay: tuple[float, float] = (1.0, 3.0)):
        self.delay = delay
        logger.info(f"Initialized {self.SOURCE_NAME} crawler")

    def _sleep(self):
        sleep_time = random.uniform(*self.delay)
        logger.debug(f"Sleeping for {sleep_time:.2f}s")
        time.sleep(sleep_time)

    @abstractmethod
    def fetch_realtime_price(self, symbol: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def fetch_historical_price(self, symbol: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def fetch_financial_info(self, symbol: str) -> Dict[str, Any]:
        pass
