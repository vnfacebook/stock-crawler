from src.crawlers.vndirect import VNDirectCrawler
from src.utils.logger import logger
import json

def test_crawler():
    crawler = VNDirectCrawler()
    
    # Mã chứng khoán thử nghiệm (Ví dụ: VND, FPT, VNM)
    symbol = "FPT"
    
    logger.info("--- Testing Realtime Price ---")
    realtime_data = crawler.fetch_realtime_price(symbol)
    print(json.dumps(realtime_data, indent=2, ensure_ascii=False))
    
    logger.info("--- Testing Historical Price (Last 5 days) ---")
    import datetime
    end_date = datetime.date.today().strftime("%Y-%m-%d")
    start_date = (datetime.date.today() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    
    historical_data = crawler.fetch_historical_price(symbol, start_date, end_date)
    print(f"Fetched {len(historical_data)} records.")
    if historical_data:
        print(json.dumps(historical_data[0], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_crawler()
