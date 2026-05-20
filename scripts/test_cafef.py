from src.crawlers.cafef import CafefCrawler
from src.utils.logger import logger
import json

def test_cafef():
    crawler = CafefCrawler()
    
    symbol = "FPT"
    
    logger.info(f"--- Testing Cafef Scraping for {symbol} ---")
    data = crawler.fetch_realtime_price(symbol)
    print("Latest transaction data:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    logger.info("--- Testing Cafef Historical Data (Page 1) ---")
    history = crawler.fetch_historical_price(symbol, "", "")
    print(f"Fetched {len(history)} records.")
    if history:
        print("First record:")
        print(json.dumps(history[0], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_cafef()
