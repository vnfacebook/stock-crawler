import os
from typing import Any, List, Dict
import datetime
from src.crawlers.base import BaseCrawler
from src.utils.http_client import HttpClient
from src.utils.logger import logger

class SSICrawler(BaseCrawler):
    SOURCE_NAME = "SSI"
    # iBoard API công khai làm fallback
    IBOARD_BASE_URL = "https://iboard.ssi.com.vn/api/v1"
    # SSI Fast Connect API chính thức
    FC_BASE_URL = "https://fc-data.ssi.com.vn/api/v2/Market"

    def __init__(self, delay: tuple[float, float] = (0.5, 1.5)):
        super().__init__(delay)
        self.api_key = os.getenv("SSI_API_KEY")
        self.secret_key = os.getenv("SSI_SECRET_KEY")
        
        self.headers = {
            "Referer": "https://iboard.ssi.com.vn/",
            "Origin": "https://iboard.ssi.com.vn",
        }
        
        self.access_token = None
        self.token_expiry = None

        if self.api_key and self.secret_key and self.api_key != "your_api_key" and self.secret_key != "your_secret_key":
            logger.info("SSI Official API credentials detected. Initializing OAuth2 mode.")
            self.use_official_api = True
        else:
            logger.info("No SSI Official API credentials configured (or using dummy values). Falling back to iBoard public API mode.")
            self.use_official_api = False

    def _get_access_token(self) -> str:
        """
        Lấy Access Token thông qua OAuth2 từ SSI Fast Connect API.
        Có cơ chế cache token dựa trên thời gian hết hạn (expiresIn).
        """
        if not self.use_official_api:
            return ""

        # Kiểm tra nếu token còn hiệu lực (bớt đi 60s an toàn)
        if self.access_token and self.token_expiry and datetime.datetime.now() < self.token_expiry:
            return self.access_token

        url = "https://fc-data.ssi.com.vn/api/v2/Market/AccessToken"
        payload = {
            "consumerKey": self.api_key,
            "consumerSecret": self.secret_key
        }

        try:
            logger.info("Requesting new Access Token from SSI Fast Connect...")
            headers = {"Content-Type": "application/json"}
            response = HttpClient.post(url, json_data=payload, headers=headers)
            res_json = response.json()
            
            # Response format: {"data": {"accessToken": "...", "expiresIn": 3600}, "message": "...", "status": "..."}
            data = res_json.get("data", {})
            token = data.get("accessToken")
            expires_in = data.get("expiresIn", 3600)
            
            if token:
                self.access_token = token
                self.token_expiry = datetime.datetime.now() + datetime.timedelta(seconds=int(expires_in) - 60)
                logger.info("Successfully retrieved SSI Access Token.")
                return self.access_token
            else:
                logger.error(f"Failed to parse Access Token from SSI response: {res_json}")
                return ""
        except Exception as e:
            logger.error(f"Error fetching SSI Access Token: {str(e)}")
            return ""

    def fetch_realtime_price(self, symbol: str) -> Dict[str, Any]:
        """
        Lấy giá thời gian thực từ SSI.
        Nếu dùng API chính thức, gọi endpoint: /Market/Securities
        Nếu dùng iBoard công khai, gọi endpoint: /stock/symbol/{symbol}
        """
        if self.use_official_api:
            token = self._get_access_token()
            if token:
                # API chính thức
                url = f"{self.FC_BASE_URL}/Securities"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                params = {"lookupSymbol": symbol}
                try:
                    logger.info(f"Fetching realtime price for {symbol} from SSI Official API")
                    response = HttpClient.get(url, params=params, headers=headers)
                    data = response.json().get("data", [])
                    return data[0] if isinstance(data, list) and len(data) > 0 else data
                except Exception as e:
                    logger.error(f"Error calling SSI Official Securities API: {str(e)}. Falling back to public API.")
            
        # Fallback về iBoard công khai
        url = f"{self.IBOARD_BASE_URL}/stock/symbol/{symbol}"
        try:
            logger.info(f"Fetching realtime price for {symbol} from SSI iBoard public API")
            response = HttpClient.get(url, headers=self.headers)
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            return data
        except Exception as e:
            logger.error(f"Error fetching SSI public realtime price for {symbol}: {str(e)}")
            return {}

    def fetch_historical_price(self, symbol: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        Lấy lịch sử giá (Daily OHLC).
        from_date, to_date có định dạng: YYYY-MM-DD
        Nếu dùng API chính thức, gọi endpoint: /Market/DailyOHLC
        Nếu dùng iBoard công khai, trả về rỗng vì iBoard không hỗ trợ API lịch sử dễ dàng.
        """
        if self.use_official_api:
            token = self._get_access_token()
            if token:
                url = f"{self.FC_BASE_URL}/DailyOHLC"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                # Chuyển YYYY-MM-DD sang DD/MM/YYYY cho đúng định dạng SSI Fast Connect
                try:
                    fd = datetime.datetime.strptime(from_date, "%Y-%m-%d").strftime("%d/%m/%Y")
                    td = datetime.datetime.strptime(to_date, "%Y-%m-%d").strftime("%d/%m/%Y")
                except ValueError:
                    fd = from_date
                    td = to_date
                    
                params = {
                    "symbol": symbol,
                    "fromDate": fd,
                    "toDate": td,
                    "pageIndex": 1,
                    "pageSize": 1000
                }
                try:
                    logger.info(f"Fetching historical price for {symbol} ({from_date} to {to_date}) from SSI Official API")
                    response = HttpClient.get(url, params=params, headers=headers)
                    # Định dạng SSI trả về thường là: {"data": [...], "totalRecords": 0}
                    return response.json().get("data", [])
                except Exception as e:
                    logger.error(f"Error fetching historical price from SSI Official API: {str(e)}")
                    return []
                    
        logger.warning("SSI iBoard Public API does not support easy historical price fetching. Please configure Official API Keys.")
        return []

    def fetch_financial_info(self, symbol: str) -> Dict[str, Any]:
        """
        Lấy thông tin tài chính cơ bản từ SSI.
        iBoard công khai hỗ trợ endpoint: /stock/finance/{symbol}
        """
        url = f"{self.IBOARD_BASE_URL}/stock/finance/{symbol}"
        try:
            logger.info(f"Fetching financial info for {symbol} from SSI iBoard public API")
            response = HttpClient.get(url, headers=self.headers)
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching SSI financial info for {symbol}: {str(e)}")
            return {}

