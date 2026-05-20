from typing import Any, List, Dict
from src.crawlers.base import BaseCrawler
from src.utils.http_client import HttpClient
from src.utils.logger import logger

class SSICrawler(BaseCrawler):
    SOURCE_NAME = "SSI"
    BASE_URL = "https://iboard.ssi.com.vn/api/v1"

    def __init__(self, delay: tuple[float, float] = (0.5, 1.5)):
        super().__init__(delay)
        self.headers = {
            "Referer": "https://iboard.ssi.com.vn/",
            "Origin": "https://iboard.ssi.com.vn",
        }

    def fetch_realtime_price(self, symbol: str) -> Dict[str, Any]:
        """
        Lấy giá thời gian thực từ iBoard SSI.
        Dùng endpoint: /stock/symbol/{symbol}
        """
        url = f"{self.BASE_URL}/stock/symbol/{symbol}"
        
        try:
            logger.info(f"Fetching realtime price for {symbol} from {self.SOURCE_NAME}")
            response = HttpClient.get(url, headers=self.headers)
            # SSI returns a list of symbols even for one symbol request
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            return data
        except Exception as e:
            logger.error(f"Error fetching SSI realtime price for {symbol}: {str(e)}")
            return {}

    def fetch_historical_price(self, symbol: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        SSI iBoard API chủ yếu cho real-time. 
        Lịch sử giá thường dùng endpoint khác hoặc nguồn khác.
        """
        logger.warning("SSI iBoard API does not support easy historical price fetching via this endpoint.")
        return []

    def fetch_financial_info(self, symbol: str) -> Dict[str, Any]:
        """
        Lấy thông tin tài chính cơ bản từ SSI.
        """
        # SSI cũng có endpoint cho tài chính cơ bản
        url = f"{self.BASE_URL}/stock/finance/{symbol}"
        try:
            logger.info(f"Fetching financial info for {symbol} from SSI")
            response = HttpClient.get(url, headers=self.headers)
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching SSI financial info for {symbol}: {str(e)}")
            return {}
