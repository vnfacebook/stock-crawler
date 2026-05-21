from typing import Any, List, Dict
from vnstock import Finance
from src.crawlers.base import BaseCrawler
from src.utils.logger import logger
import datetime
import pandas as pd

class VietstockCrawler(BaseCrawler):
    SOURCE_NAME = "Vietstock/TCBS"

    def __init__(self, delay: tuple[float, float] = (0.5, 1.5)):
        super().__init__(delay)

    def fetch_realtime_price(self, symbol: str) -> Dict[str, Any]:
        """
        Vietstock tập trung vào báo cáo tài chính, không tối ưu cho giá realtime.
        """
        logger.warning("VietstockCrawler is optimized for financial reporting, not real-time prices.")
        return {}

    def fetch_historical_price(self, symbol: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        Vietstock tập trung vào báo cáo tài chính, không tối ưu cho lịch sử giá.
        """
        logger.warning("VietstockCrawler is optimized for financial reporting, not historical prices.")
        return []

    def fetch_financial_info(self, symbol: str) -> Dict[str, Any]:
        """
        Lấy thông tin chỉ số tài chính cơ bản và chuyên sâu của doanh nghiệp.
        Chuẩn hóa dữ liệu về schema cố định (Method B) giống VnstockCrawler.
        """
        try:
            logger.info(f"Fetching financial info for {symbol} from {self.SOURCE_NAME}")
            
            # Sử dụng module Finance của thư viện vnstock kết nối với nguồn TCBS/Vietstock
            f = Finance(symbol=symbol, source='TCBS')
            df = f.ratio(period='yearly')
            
            if df.empty:
                logger.warning(f"No yearly financial ratio found for {symbol} from TCBS/Vietstock")
                return {}
            
            # Lọc ra danh sách các cột là năm (chữ số)
            year_cols = [c for c in df.columns if str(c).isdigit()]
            if not year_cols:
                logger.warning(f"No yearly data columns found for {symbol}")
                return {}
            
            latest_year = year_cols[-1]
            
            # Khởi tạo schema cố định giống VnstockCrawler để đảm bảo tương thích BigQuery
            important_indices = {
                'roa': 'roa',
                'roe': 'roe',
                'pe': 'pe',
                'pb': 'pb',
                'eps': 'eps',
                'quickRatio': 'quick_ratio',
                'currentRatio': 'current_ratio',
                'grossProfitMargin': 'gross_margin',
                'netProfitMargin': 'net_margin',
                'debtOnEquity': 'debt_to_equity'
            }

            normalized_data = {
                'symbol': symbol,
                'report_year': latest_year,
                'fetched_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # Map dữ liệu từ DataFrame vào schema cố định
            for _, row in df.iterrows():
                item_id = row.get('item_id')
                if item_id in important_indices:
                    col_name = important_indices[item_id]
                    val = row.get(latest_year)
                    
                    # Xử lý nếu val là một Series
                    if isinstance(val, pd.Series):
                        val = val.iloc[0]
                    
                    # Ép kiểu dữ liệu về float
                    try:
                        normalized_data[col_name] = float(val) if val is not None else None
                    except (ValueError, TypeError):
                        normalized_data[col_name] = val

            logger.info(f"Successfully fetched and normalized financial info for {symbol} from {self.SOURCE_NAME}")
            return normalized_data
        except Exception as e:
            logger.error(f"Error in VietstockCrawler for {symbol}: {str(e)}")
            return {}
