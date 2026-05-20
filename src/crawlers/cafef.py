from typing import Any, List, Dict
from playwright.sync_api import sync_playwright
from src.crawlers.base import BaseCrawler
from src.utils.logger import logger
import time

class CafefCrawler(BaseCrawler):
    SOURCE_NAME = "Cafef"
    BASE_URL = "https://s.cafef.vn"

    def __init__(self, delay: tuple[float, float] = (2.0, 5.0)):
        super().__init__(delay)

    def fetch_realtime_price(self, symbol: str) -> Dict[str, Any]:
        """
        Lấy giá và thông tin cơ bản từ Cafef bằng Playwright.
        """
        url = f"{self.BASE_URL}/Lich-su-giao-dich-{symbol}-1.chn"
        data = {"symbol": symbol}
        
        try:
            with sync_playwright() as p:
                logger.info(f"Opening browser to fetch {symbol} from {self.SOURCE_NAME}")
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Chờ bảng dữ liệu xuất hiện
                page.wait_for_selector("table", timeout=10000)
                
                # Lấy dữ liệu từ dòng đầu tiên của bảng lịch sử giao dịch
                # Cafef thường dùng table có class hoặc cấu trúc td cụ thể
                rows = page.query_selector_all("tr")
                for row in rows:
                    cols = row.query_selector_all("td")
                    if len(cols) > 10:
                        # Kiểm tra xem có phải dòng dữ liệu không (thường cột 1 là ngày dd/mm/yyyy)
                        date_text = cols[0].inner_text().strip()
                        if "/" in date_text:
                            data["date"] = date_text
                            data["close"] = cols[1].inner_text().strip()
                            data["change"] = cols[2].inner_text().strip()
                            data["volume"] = cols[10].inner_text().strip()
                            data["open"] = cols[4].inner_text().strip()
                            data["high"] = cols[5].inner_text().strip()
                            data["low"] = cols[6].inner_text().strip()
                            break
                
                browser.close()
                return data
        except Exception as e:
            logger.error(f"Playwright error scraping Cafef for {symbol}: {str(e)}")
            return data

    def fetch_historical_price(self, symbol: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        Lấy lịch sử giao dịch trang đầu tiên.
        """
        url = f"{self.BASE_URL}/Lich-su-giao-dich-{symbol}-1.chn"
        results = []
        
        try:
            with sync_playwright() as p:
                logger.info(f"Fetching historical data for {symbol} via Playwright")
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=60000)
                
                rows = page.query_selector_all("tr")
                for row in rows:
                    cols = row.query_selector_all("td")
                    if len(cols) > 10:
                        date_text = cols[0].inner_text().strip()
                        if "/" in date_text:
                            results.append({
                                "date": date_text,
                                "close": cols[1].inner_text().strip(),
                                "change": cols[2].inner_text().strip(),
                                "volume": cols[10].inner_text().strip(),
                                "open": cols[4].inner_text().strip(),
                                "high": cols[5].inner_text().strip(),
                                "low": cols[6].inner_text().strip()
                            })
                browser.close()
            return results
        except Exception as e:
            logger.error(f"Playwright error fetching historical price: {str(e)}")
            return []

    def fetch_financial_info(self, symbol: str) -> Dict[str, Any]:
        logger.info("Financial info via Playwright not implemented yet.")
        return {"symbol": symbol}
