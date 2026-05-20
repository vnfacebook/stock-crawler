from typing import List, Dict
from vnstock import Listing
from src.crawlers.base import BaseCrawler
from src.utils.logger import logger
import pandas as pd

class MarketInfo:
    def __init__(self):
        self.listing = Listing()

    def get_all_symbols(self) -> List[str]:
        """
        Lấy danh sách tất cả các mã chứng khoán đang niêm yết trên HOSE, HNX, UPCOM.
        """
        try:
            logger.info("Fetching all stock symbols from market...")
            # Lấy danh sách tất cả các công ty niêm yết
            df = self.listing.all_symbols()
            if not df.empty:
                # Lọc ra danh sách các mã (Ticker/Symbol)
                symbols = df['symbol'].tolist()
                logger.info(f"Total symbols found: {len(symbols)}")
                return symbols
            return []
        except Exception as e:
            logger.error(f"Error fetching symbols: {str(e)}")
            return []

    def get_companies_info(self) -> pd.DataFrame:
        """
        Lấy thông tin chi tiết các công ty (Tên, ngành, sàn niêm yết).
        """
        try:
            df = self.listing.all_symbols()
            return df
        except Exception as e:
            logger.error(f"Error fetching company info: {str(e)}")
            return pd.DataFrame()
