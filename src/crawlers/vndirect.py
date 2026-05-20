from typing import Any, List, Dict
from src.crawlers.base import BaseCrawler
from src.utils.http_client import HttpClient
from src.utils.logger import logger

class VNDirectCrawler(BaseCrawler):
    SOURCE_NAME = "VNDirect"
    BASE_URL = "https://finfo-api.vndirect.com.vn/v4"

    def __init__(self, delay: tuple[float, float] = (0.5, 1.5)):
        super().__init__(delay)

    def fetch_realtime_price(self, symbol: str) -> Dict[str, Any]:
        """
        Lấy giá thời gian thực của một mã chứng khoán.
        Sử dụng endpoint: /stock_prices
        """
        url = f"{self.BASE_URL}/stock_prices"
        params = {
            "q": f"code:{symbol}",
            "size": 1
        }
        
        try:
            logger.info(f"Fetching realtime price for {symbol} from {self.SOURCE_NAME}")
            response = HttpClient.get(url, params=params)
            data = response.json().get("data", [])
            if data:
                return data[0]
            logger.warning(f"No data found for symbol: {symbol}")
            return {}
        except Exception as e:
            logger.error(f"Error fetching realtime price for {symbol}: {str(e)}")
            return {}

    def fetch_historical_price(self, symbol: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        Lấy lịch sử giá của một mã chứng khoán.
        from_date, to_date định dạng: YYYY-MM-DD
        """
        url = f"{self.BASE_URL}/stock_prices"
        params = {
            "q": f"code:{symbol}~date:gte:{from_date}~date:lte:{to_date}",
            "size": 1000,
            "sort": "date:desc"
        }
        
        try:
            logger.info(f"Fetching historical price for {symbol} from {from_date} to {to_date}")
            response = HttpClient.get(url, params=params)
            return response.json().get("data", [])
        except Exception as e:
            logger.error(f"Error fetching historical price for {symbol}: {str(e)}")
            return []

    def fetch_financial_info(self, symbol: str) -> Dict[str, Any]:
        """
        Lấy thông tin tài chính cơ bản.
        """
        # VNDirect có nhiều endpoint khác nhau cho tài chính, tạm thời lấy snapshot cơ bản
        url = f"{self.BASE_URL}/financial_indicators"
        params = {
            "q": f"code:{symbol}",
            "size": 1,
            "sort": "reportDate:desc"
        }
        
        try:
            logger.info(f"Fetching financial info for {symbol}")
            response = HttpClient.get(url, params=params)
            data = response.json().get("data", [])
            return data[0] if data else {}
        except Exception as e:
            logger.error(f"Error fetching financial info for {symbol}: {str(e)}")
            return {}
