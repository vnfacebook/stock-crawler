from typing import Any, List, Dict
from vnstock import Quote, Finance
import pandas as pd
from src.crawlers.base import BaseCrawler
from src.utils.logger import logger
import datetime

class VnstockCrawler(BaseCrawler):
    SOURCE_NAME = "Vnstock (VCI/KBS)"

    def __init__(self, delay: tuple[float, float] = (0.5, 1.5)):
        super().__init__(delay)

    def fetch_realtime_price(self, symbol: str) -> Dict[str, Any]:
        """
        Lấy giá thời gian thực bằng API chuẩn của vnstock v4.
        """
        try:
            logger.info(f"Fetching realtime price for {symbol}")
            q = Quote(symbol=symbol, source='VCI')
            df = q.history(period='1d', interval='1m')
            if not df.empty:
                latest = df.iloc[-1].to_dict()
                return latest
            return {}
        except Exception as e:
            logger.error(f"Error fetching realtime price: {str(e)}")
            return {}

    def fetch_historical_price(self, symbol: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        Lấy lịch sử giá.
        """
        try:
            logger.info(f"Fetching historical price for {symbol} ({from_date} to {to_date})")
            q = Quote(symbol=symbol, source='VCI')
            df = q.history(start=from_date, end=to_date, interval='1D')
            if not df.empty:
                df = df.reset_index()
                # Luôn gán symbol vào DataFrame trước khi trả về
                df['symbol'] = symbol
                return df.to_dict('records')
            return []
        except Exception as e:
            logger.error(f"Error fetching historical price: {str(e)}")
            return []

    def fetch_financial_info(self, symbol: str) -> Dict[str, Any]:
        """
        Lấy chỉ số tài chính và chuẩn hóa về schema cố định (Method B).
        """
        try:
            logger.info(f"Fetching financial info for {symbol}")
            f = Finance(symbol=symbol, source='VCI')
            df = f.ratio(period='yearly')
            
            if df.empty:
                return {}

            # Chuẩn hóa: Lấy danh sách các cột là năm (chữ số)
            year_cols = [c for c in df.columns if str(c).isdigit()]
            if not year_cols:
                logger.warning(f"No yearly data found for {symbol}")
                return {}
            
            latest_year = year_cols[-1]
            
            # Schema cố định cho các chỉ số quan trọng
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

            # Map dữ liệu từ API vào schema cố định
            for _, row in df.iterrows():
                item_id = row.get('item_id')
                if item_id in important_indices:
                    col_name = important_indices[item_id]
                    val = row.get(latest_year)
                    
                    # Xử lý nếu val là một Series (do trùng tên cột năm)
                    if isinstance(val, pd.Series):
                        val = val.iloc[0]
                    
                    # Ép kiểu về float nếu có thể, nếu không giữ nguyên (None/NaN)
                    try:
                        normalized_data[col_name] = float(val) if val is not None else None
                    except (ValueError, TypeError):
                        normalized_data[col_name] = val

            return normalized_data
        except Exception as e:
            logger.error(f"Error fetching financial info for {symbol}: {str(e)}")
            return {}
